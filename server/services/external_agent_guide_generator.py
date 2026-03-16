"""
External Agent Integration Guide Generator
===========================================

Generates dynamic integration guides for external agents based on current
SeaForge configuration. Supports Agent Zero and generic FastA2A agents.
"""

from typing import Literal
from datetime import datetime


class ExternalAgentGuideGenerator:
    """Generates integration guides for external agents."""
    
    def __init__(
        self,
        seaforge_connection_type: str = "docker_network",
        seaforge_container_name: str = "seaforge",
        seaforge_host: str = "localhost",
        seaforge_port: int = 30003,
        seaforge_url_override: str = None,
        project_name: str = None,
        task_code: str = None
    ):
        self.connection_type = seaforge_connection_type
        self.container_name = seaforge_container_name
        self.host = seaforge_host
        self.port = seaforge_port
        self.url_override = seaforge_url_override
        
        # Determine SeaForge base URL
        if seaforge_url_override:
            self.seaforge_base_url = seaforge_url_override
        elif seaforge_connection_type == "docker_network":
            self.seaforge_base_url = f"http://{seaforge_container_name}:{seaforge_port}"
        else:
            self.seaforge_base_url = f"http://{seaforge_host}:{seaforge_port}"
        
        self.project_name = project_name
        self.task_code = task_code
    
    def generate_guide(
        self,
        agent_type: Literal["agent_zero", "generic"] = "agent_zero",
        format: Literal["markdown", "plain"] = "markdown"
    ) -> str:
        """Generate integration guide for external agent."""
        
        if agent_type == "agent_zero":
            guide = self._generate_agent_zero_guide()
        else:
            guide = self._generate_generic_guide()
        
        if format == "plain":
            # Strip markdown formatting
            guide = guide.replace("#", "").replace("**", "").replace("`", "")
        
        return guide
    
    def _generate_agent_zero_guide(self) -> str:
        """Generate Agent Zero specific integration guide."""
        
        network_section = self._generate_network_section()
        
        guide = f"""# Agent Zero ↔ SeaForge Integration Guide
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 1. Connection Details

**SeaForge Configuration:**
- Host: {self.host}
- Port: {self.port}
- Base URL: `{self.seaforge_base_url}`
- A2A Endpoint: `{self.seaforge_base_url}/a2a`
- SSE Stream: `{self.seaforge_base_url}/a2a/stream`

**Your Agent Zero Configuration:**
- Base URL: `http://localhost:50001` (or your Agent Zero host)
- A2A Endpoint: `http://localhost:50001/a2a/t-{{API-TOKEN}}`
- SSE Stream: `http://localhost:50001/a2a/stream`
- Required Skill: **GB01** (Gitbot skill)

---

{network_section}

---

## 3. Task ID Scheme (IMPORTANT)

### Planning Phase: 000-099
- Initial feature breakdown
- Spec refinement iterations
- **No Pull Requests created**
- Branch pattern: `{{TASK-CODE}}-{{000-099}}-{{DD/MM/YY}}`

### Development Phase: 100+
- Feature implementation
- **Pull Requests created to main**
- Branch pattern: `{{TASK-CODE}}-{{100+}}-{{DD/MM/YY}}`

**Examples:**
```
SF001-000-11/03/26  (Planning - no PR)
SF001-001-11/03/26  (Planning - no PR)
SF001-100-11/03/26  (Development - PR #1)
SF001-101-11/03/26  (Development - PR #2)
```

---

## 4. How You Receive Tasks from SeaForge

SeaForge will send tasks to your A2A endpoint using the **GB01 skill**:

```http
POST http://localhost:50001/a2a/t-{{YOUR-API-TOKEN}}
Content-Type: application/json

{{
  "message": "GB01\\n\\nTASK_CODE: SF001\\nTASK_ID: 105\\nTASK_TYPE: development\\nREPO_URL: https://github.com/user/repo\\nAUTH_TOKEN: ghp_xxx\\nPREVIOUS_BRANCH: SF001-104-11/03/26\\nBRANCH_NAME: SF001-105-11/03/26\\nCOMMIT_MESSAGE: feat(105): Implement feature\\n\\nFeature description here...",
  "context_id": "seaforge-project-{{project}}-{{task_id}}",
  "reset": false
}}
```

**Key Fields to Extract:**
- `GB01` - Skill invocation (first line)
- `TASK_CODE` - Project identifier
- `TASK_ID` - Sequential task number (000-099 planning, 100+ development)
- `TASK_TYPE` - "planning" or "development"
- `REPO_URL` - GitHub repository URL
- `AUTH_TOKEN` - GitHub Personal Access Token
- `PREVIOUS_BRANCH` - Branch to cherry-pick from
- `BRANCH_NAME` - New branch to create
- `COMMIT_MESSAGE` - Commit message to use

---

## 5. Git Workflow (Gitbot GB01)

**Every task follows this exact workflow:**

```bash
# 1. Ensure main branch exists
git fetch origin main 2>/dev/null || {{
  git checkout --orphan main
  git commit --allow-empty -m "init: main branch"
  git push origin main
}}

# 2. Set git identity (agent-specific)
git config user.name "Agent Zero Gitbot"
git config user.email "gitbot@agentzero.ai"

# 3. Create branch from main
git fetch origin main
git checkout -b {{BRANCH_NAME}} origin/main

# 4. Cherry-pick from previous branch
git fetch origin {{PREVIOUS_BRANCH}}
git log origin/{{PREVIOUS_BRANCH}} --pretty=format:"%H" --reverse | while read commit; do
  git cherry-pick $commit --no-commit || {{
    # Conflict: use theirs strategy
    git checkout --theirs .
    git add -A
    git commit -m "cherry-pick: $commit (resolved)"
  }}
done

# 5. Implement feature (your work here)

# 6. Commit changes (only if files changed)
git add -A
if ! git diff --cached --quiet; then
  git commit -m "{{COMMIT_MESSAGE}}"
fi

# 7. Push to GitHub (never force)
git push origin {{BRANCH_NAME}}

# 8. Create PR if development phase (TASK_ID >= 100)
if [ $TASK_ID -ge 100 ]; then
  # GitHub API: Create PR to main
  curl -X POST https://api.github.com/repos/{{owner}}/{{repo}}/pulls \\
    -H "Authorization: token {{AUTH_TOKEN}}" \\
    -H "Accept: application/vnd.github.v3+json" \\
    -d '{{
      "title": "{{COMMIT_MESSAGE}}",
      "head": "{{BRANCH_NAME}}",
      "base": "main",
      "body": "Automated PR from Agent Zero Gitbot"
    }}'
fi
```

---

## 6. How to Communicate Back to SeaForge

### Method 1: Real-Time Progress (SSE Stream)

SeaForge subscribes to your SSE stream automatically. Just stream your progress:

```
data: {{"message": "Gitbot: Creating branch SF001-105-11/03/26"}}
data: {{"message": "Gitbot: Cherry-picking 8 commits from SF001-104"}}
data: {{"message": "Gitbot: Implementing feature..."}}
data: {{"message": "Gitbot: Committing changes"}}
data: {{"message": "Gitbot: Pushing to GitHub"}}
data: {{"message": "Gitbot: Creating PR #15"}}
data: {{"message": "✅ Gitbot Task Complete: SF001-105"}}
```

### Method 2: Completion Notification (Required)

When task completes, send this to SeaForge:

```http
POST {self.seaforge_base_url}/a2a
Content-Type: application/json

{{
  "message": "✅ Gitbot Task Complete: SF001-105\\n📁 Branch: SF001-105-11/03/26\\n🔨 Commit Hash: abc123def456\\n📄 Files Changed:\\n   - src/todos/delete.tsx\\n   - src/api/todos.ts\\n🍒 Cherry-Picked: 8 commits from SF001-104-11/03/26\\n🔗 Merge Request: https://github.com/user/repo/pull/15",
  "context_id": "seaforge-project-{{project}}-105"
}}
```

**Required Response Format:**
```
✅ Gitbot Task Complete: {{TASK-CODE}}-{{TASK-ID}}
📁 Branch: {{BRANCH_NAME}}
🔨 Commit Hash: {{commit-hash}}
📄 Files Changed:
   - file1.tsx
   - file2.ts
🍒 Cherry-Picked: {{count}} commits from {{PREVIOUS-BRANCH}}
🔗 Merge Request: {{PR-URL}}
```

---

## 7. Error Handling

If task fails, send error notification:

```http
POST {self.seaforge_base_url}/a2a
Content-Type: application/json

{{
  "message": "❌ Gitbot Task Failed: SF001-105\\nError: Cherry-pick conflict could not be resolved\\nBranch: SF001-105-11/03/26 (partial)\\nDetails: ...",
  "context_id": "seaforge-project-{{project}}-105"
}}
```

---

## 8. Testing the Integration

### Test 1: Verify A2A Endpoint

```bash
curl -X POST {self.seaforge_base_url}/a2a \\
  -H "Content-Type: application/json" \\
  -d '{{"message": "Test connection", "context_id": "test-1"}}'
```

Expected: `{{"message": "Acknowledged", "context_id": "test-1"}}`

### Test 2: Subscribe to SSE Stream

```bash
curl {self.seaforge_base_url}/a2a/stream
```

Expected: SSE events stream

---

## 9. Quick Start Checklist

- [ ] Note SeaForge URL: `{self.seaforge_base_url}`
- [ ] Configure your A2A endpoint to receive tasks
- [ ] Enable SSE streaming for progress updates
- [ ] Implement GB01 skill handler (Gitbot workflow)
- [ ] Test connection to SeaForge's `/a2a` endpoint
- [ ] Verify git operations work
- [ ] Test sending completion notification to SeaForge
- [ ] Monitor SSE stream for real-time feedback

---

**Generated by SeaForge v1.0**
**Integration Guide Generator**
"""
        
        return guide
    
    def _generate_generic_guide(self) -> str:
        """Generate generic FastA2A integration guide."""
        
        guide = f"""# External Agent ↔ SeaForge Integration Guide
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Connection Details

**SeaForge Configuration:**
- Base URL: `{self.seaforge_base_url}`
- A2A Endpoint: `{self.seaforge_base_url}/a2a`
- SSE Stream: `{self.seaforge_base_url}/a2a/stream`
- Protocol: FastA2A v0.2+

**Your Agent Configuration:**
- Implement A2A endpoint: `http://your-agent:port/a2a`
- Implement SSE stream: `http://your-agent:port/a2a/stream`
- Support bidirectional communication

---

## Task Reception

SeaForge will send tasks via POST to your A2A endpoint:

```http
POST http://your-agent:port/a2a
Content-Type: application/json

{{
  "message": "Task description in natural language or structured format",
  "context_id": "seaforge-{{project}}-{{task_id}}",
  "reset": false
}}
```

**You should:**
1. Parse the task message
2. Execute the task
3. Stream progress via SSE
4. Send completion to SeaForge's A2A endpoint

---

## Progress Streaming

Stream progress via SSE (SeaForge subscribes automatically):

```
data: {{"message": "Starting task..."}}
data: {{"message": "Progress update..."}}
data: {{"message": "Task complete"}}
```

---

## Completion Notification

Send completion to SeaForge:

```http
POST {self.seaforge_base_url}/a2a
Content-Type: application/json

{{
  "message": "Task completed successfully. Results: ...",
  "context_id": "seaforge-{{project}}-{{task_id}}"
}}
```

---

**Generated by SeaForge v1.0**
"""
        
        return guide
    
    def _generate_network_section(self) -> str:
        """Generate network configuration section based on connection type."""
        
        if self.connection_type == "docker_network":
            return f"""## 2. Network Configuration: Docker Network

**Deployment Type:** Same Docker Network

**Setup:**
Both SeaForge and your agent must be on the same Docker network.

```yaml
# docker-compose.yml
version: '3.8'

services:
  seaforge:
    container_name: {self.container_name}
    networks:
      - agent-network
    ports:
      - "{self.port}:{self.port}"

  your-agent:
    container_name: your-agent-name
    networks:
      - agent-network
    ports:
      - "50001:50001"

networks:
  agent-network:
    driver: bridge
```

**Connection URLs:**
- SeaForge → Your Agent: `http://your-agent-name:50001/a2a`
- Your Agent → SeaForge: `http://{self.container_name}:{self.port}/a2a`

**No nginx or ngrok needed** - Docker DNS handles everything!
"""
        
        elif self.connection_type == "direct_ip":
            return f"""## 2. Network Configuration: Direct IP

**Deployment Type:** Different Hosts (LAN/VPN)

**Setup:**
Ensure both hosts can reach each other on the network.

**SeaForge Host:** {self.host}:{self.port}
**Your Agent Host:** (your IP):50001

**Firewall Rules:**
- Allow inbound TCP {self.port} on SeaForge host
- Allow inbound TCP 50001 on your agent host

**Connection URLs:**
- SeaForge → Your Agent: `http://<your-agent-ip>:50001/a2a`
- Your Agent → SeaForge: `http://{self.host}:{self.port}/a2a`

**Optional:** Use nginx for SSL/TLS encryption in production.
"""
        
        elif self.connection_type == "domain":
            return f"""## 2. Network Configuration: Domain Names

**Deployment Type:** Production (with nginx/SSL)

**Setup:**
Use nginx reverse proxy with SSL certificates.

**SeaForge Domain:** {self.host}
**Your Agent Domain:** (your domain)

**Nginx Configuration (SeaForge):**
```nginx
server {{
    listen 443 ssl;
    server_name {self.host};
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /a2a {{
        proxy_pass http://{self.container_name}:{self.port}/a2a;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
    
    location /a2a/stream {{
        proxy_pass http://{self.container_name}:{self.port}/a2a/stream;
        proxy_buffering off;
        proxy_cache off;
    }}
}}
```

**Connection URLs:**
- SeaForge → Your Agent: `https://<your-domain>/a2a`
- Your Agent → SeaForge: `https://{self.host}/a2a`
"""
        
        return ""
