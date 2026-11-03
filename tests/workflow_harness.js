// Runs an actions/github-script body against a fake GitHub API.
// stdin: {"script": "...", "context": {...}, "fake": {...}, "env": {...}}
// stdout: {"calls": [...], "failed": "<setFailed message or null>"}
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;

function fakeGithub({ issues = {}, openCount = 0, assignable = true, comments = [] }, calls) {
  return {
    rest: {
      issues: {
        createComment: async ({ body }) => calls.push({ op: "createComment", body }),
        updateComment: async ({ comment_id, body }) => calls.push({ op: "updateComment", comment_id, body }),
        listComments: async () => ({ data: comments }),
        addAssignees: async ({ assignees }) => {
          calls.push({ op: "addAssignees", assignees });
          return { data: { assignees: assignable ? assignees.map((login) => ({ login })) : [] } };
        },
        removeAssignees: async ({ assignees }) => calls.push({ op: "removeAssignees", assignees }),
        get: async ({ issue_number }) => {
          const issue = issues[String(issue_number)];
          if (!issue) throw Object.assign(new Error("Not Found"), { status: 404 });
          return { data: issue };
        },
      },
      search: {
        issuesAndPullRequests: async () => ({ data: { total_count: openCount } }),
      },
    },
  };
}

let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", async () => {
  const { script, context, fake = {}, env = {} } = JSON.parse(input);
  Object.assign(process.env, env);
  const calls = [];
  let failed = null;
  const core = { info() {}, setFailed: (message) => (failed = message) };
  await new AsyncFunction("github", "context", "core", script)(fakeGithub(fake, calls), context, core);
  process.stdout.write(JSON.stringify({ calls, failed }));
});
