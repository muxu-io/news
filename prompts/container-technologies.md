You are creating a technical digest for a platform engineer tracking the container technologies ecosystem.

Analyze the following content from the last {time_window}.

## Reader Profile

The reader is a platform engineer who:
- Evaluates and operates container tools across development and production environments
- Makes architectural decisions about container runtimes, build systems, and registries
- Compares Docker and Podman ecosystems for tooling decisions
- Needs awareness of ecosystem direction, security updates, and breaking changes
- Values practical impact over marketing

## Projects Covered

**Docker / Moby:**
- Docker Engine (Moby), Docker Desktop
- BuildKit (next-gen image builder)

**Podman Ecosystem:**
- Podman, Podman Desktop
- Buildah (OCI image builder)
- Skopeo (image transport)

**Container Runtimes:**
- containerd (industry standard daemon)
- runc (OCI reference runtime)
- crun (lightweight C runtime)

**Standards:**
- OCI image-spec, runtime-spec, distribution-spec

**Registry:**
- Distribution (formerly Docker Registry)

## Priority Topics (always highlight)

1. **Security advisories** - CVEs, security patches, vulnerability disclosures
2. **Breaking changes** - API changes, deprecations, migration requirements
3. **Major releases** - New versions with architectural significance
4. **Cross-project patterns** - Similar changes across Docker and Podman ecosystems
5. **OCI spec changes** - Standards updates affecting compatibility
6. **Runtime security** - Rootless containers, user namespaces, seccomp, SELinux

## Secondary Topics

- Build performance improvements
- Desktop app updates (Docker Desktop, Podman Desktop)
- Kubernetes CRI integration
- Image format changes
- Registry protocol updates
- Networking and storage drivers

## Skip

- Marketing announcements without technical substance
- Minor patch releases without notable changes
- User support questions
- Tutorial and getting-started content
- Project-specific news without broader relevance

## Output Format

## Executive Summary
3-4 sentences covering the most significant developments across the ecosystem.

## Cross-Project Trends
Patterns, convergences, or divergences worth noting across Docker and Podman ecosystems. Omit if none.

## Critical/Urgent
Security issues, breaking changes, or blockers. Omit if none.

## Project Updates

Group by area when there's significant activity:

### Docker / Moby
### Podman Ecosystem
### Container Runtimes
### OCI Standards

Only include sections with meaningful content.

## Technical Discussions
Design decisions, RFCs, and architectural threads worth following.

## Guidelines

- Highlight connections between projects (e.g., "Podman adopted X, similar to Docker's...")
- Lead with technical impact
- Include links to original sources
- Flag items requiring action or testing
- Note compatibility implications across Docker/Podman
- Omit empty sections

{errors_section}

Content to analyze:
{content}
