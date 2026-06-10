import streamlit as st
from agent import run_review

st.set_page_config(
    page_title="AI Code Review Agent",
    page_icon="🔍",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .verdict-approve    { background:#d4edda; border-left:4px solid #28a745; padding:12px 16px; border-radius:4px; }
    .verdict-changes    { background:#fff3cd; border-left:4px solid #ffc107; padding:12px 16px; border-radius:4px; }
    .verdict-comment    { background:#d1ecf1; border-left:4px solid #17a2b8; padding:12px 16px; border-radius:4px; }
    .issue-bug          { border-left:4px solid #dc3545; padding:8px 12px; margin:4px 0; background:#fff5f5; border-radius:3px; }
    .issue-security     { border-left:4px solid #fd7e14; padding:8px 12px; margin:4px 0; background:#fff8f0; border-radius:3px; }
    .issue-performance  { border-left:4px solid #6f42c1; padding:8px 12px; margin:4px 0; background:#f8f0ff; border-radius:3px; }
    .issue-style        { border-left:4px solid #6c757d; padding:8px 12px; margin:4px 0; background:#f8f9fa; border-radius:3px; }
    .file-card          { border:1px solid #e0e0e0; border-radius:6px; padding:16px; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

SEVERITY_COLORS = {"bug": "🔴", "security": "🟠", "performance": "🟣", "style": "⚪"}
VERDICT_LABELS = {
    "APPROVE": ("✅ APPROVE", "verdict-approve"),
    "REQUEST_CHANGES": ("⚠️ REQUEST CHANGES", "verdict-changes"),
    "COMMENT": ("💬 COMMENT", "verdict-comment"),
}


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 AI Code Review Agent")
st.caption("Powered by Claude + LangGraph + GitHub API")
st.divider()

# ── Sidebar — credentials ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 Credentials")
    st.caption("Keys are used only for this session and never stored.")

    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get yours at console.anthropic.com",
    )
    github_token = st.text_input(
        "GitHub Token",
        type="password",
        placeholder="ghp_...",
        help="Needs repo scope. Create at github.com/settings/tokens",
    )

    st.divider()
    st.markdown("**Required GitHub token scopes**")
    st.markdown("- `repo` — for private repos\n- `public_repo` — for public repos only")

    st.divider()
    st.markdown("**Agent flow**")
    st.markdown("1. Fetch PR & diff\n2. Analyze each file\n3. Generate summary\n4. (Optional) Post to GitHub")

# ── Main — inputs ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    repo_name = st.text_input(
        "GitHub Repository",
        placeholder="owner/repo  (e.g. facebook/react)",
    )
with col2:
    pr_number = st.number_input("PR Number", min_value=1, step=1, value=None, placeholder="42")

post_to_github = st.checkbox(
    "Post review to GitHub",
    value=False,
    help="When checked, the agent will submit the review directly on the PR. Leave unchecked for a dry run.",
)

run_btn = st.button("▶  Run Review", type="primary", use_container_width=True)

# ── Validation & run ──────────────────────────────────────────────────────────
if run_btn:
    errors = []
    if not anthropic_key:
        errors.append("Anthropic API Key is required.")
    if not github_token:
        errors.append("GitHub Token is required.")
    if not repo_name or "/" not in repo_name:
        errors.append("Repository must be in `owner/repo` format.")
    if not pr_number:
        errors.append("PR Number is required.")

    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    # ── Progress display ──────────────────────────────────────────────────────
    status = st.status("Running review...", expanded=True)
    with status:
        st.write("📡 Fetching PR details from GitHub...")

    result_state = None
    error_msg = None

    try:
        with st.spinner(""):
            result_state = run_review(
                repo_name=repo_name,
                pr_number=int(pr_number),
                post_to_github=post_to_github,
                anthropic_api_key=anthropic_key,
                github_token=github_token,
            )
        status.update(label="Review complete!", state="complete", expanded=False)
    except Exception as exc:
        error_msg = str(exc)
        status.update(label="Review failed", state="error", expanded=False)

    if error_msg:
        st.error(f"**Error:** {error_msg}")
        st.stop()

    # ── PR meta ───────────────────────────────────────────────────────────────
    pr_info = result_state["pr_info"]
    st.divider()
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    meta_col1.metric("Pull Request", f"#{pr_number}")
    meta_col2.metric("Author", pr_info.get("author", "—"))
    meta_col3.metric("Files Reviewed", len(result_state["file_reviews"]))

    st.markdown(f"**[{pr_info['title']}]({pr_info['url']})**  `{pr_info['head_branch']}` → `{pr_info['base_branch']}`")

    # ── Verdict banner ─────────────────────────────────────────────────────────
    verdict = result_state["verdict"]
    label, css_class = VERDICT_LABELS.get(verdict, ("💬 COMMENT", "verdict-comment"))
    st.markdown(f'<div class="{css_class}"><strong>{label}</strong></div>', unsafe_allow_html=True)
    if post_to_github and result_state["result"] != "dry_run":
        st.success(f"Review posted to GitHub: {result_state['result']}")

    # ── Final review ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Review Summary")
    st.markdown(result_state["final_review"])

    # ── Per-file breakdown ─────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"📂 File-by-File Breakdown ({len(result_state['file_reviews'])} files)")

    for review in result_state["file_reviews"]:
        issues = review.get("issues", [])
        badge = f"{'🔴 ' + str(len(issues)) + ' issue(s)' if issues else '✅ Clean'}"

        with st.expander(f"`{review['filename']}` — {badge}"):
            st.markdown(f"**Summary:** {review['summary']}")

            if issues:
                st.markdown("**Issues found:**")
                for issue in issues:
                    sev = issue.get("severity", "style").lower()
                    icon = SEVERITY_COLORS.get(sev, "⚪")
                    css = f"issue-{sev}" if sev in SEVERITY_COLORS else "issue-style"
                    st.markdown(
                        f'<div class="{css}">{icon} <strong>Line {issue["line"]} [{sev.upper()}]</strong><br>{issue["comment"]}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No issues detected in this file.")

            st.markdown(f"**Overall:** {review['overall']}")
