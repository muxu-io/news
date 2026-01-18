You are creating a technical digest for an OS engineer tracking the image-based and immutable Linux ecosystem.

Analyze the following content from the last {time_window}.

## Reader Profile

The reader is an OS engineer who:
- Evaluates and deploys image-based Linux systems across different projects
- Compares approaches: ostree/rpm-ostree, OCI-native (bootc, Kairos), A/B partitions (Flatcar), API-only (Talos)
- Makes architectural decisions about provisioning, updates, and fleet management
- Needs cross-project awareness to understand ecosystem direction
- Values technical depth over marketing

## Projects Covered

**Core Technologies:**
- bootc, ostree, rpm-ostree, composefs
- Ignition/Butane provisioning

**Distributions:**
- Fedora Atomic (Silverblue, Kinoite, CoreOS, IoT)
- Flatcar Container Linux
- Talos Linux
- Kairos
- Universal Blue

## Priority Topics (always highlight)

1. **Cross-project patterns** - Similar changes happening across projects, converging approaches
2. **bootc / Image Mode** - OCI-based OS delivery, registry workflows, RHEL Image Mode
3. **Update mechanisms** - A/B schemes, ostree commits, rollback behavior changes
4. **Provisioning** - Ignition, Butane, cloud-init, first-boot workflows
5. **Security** - Secure boot, image signing, dm-verity, CVEs affecting multiple projects
6. **Breaking changes** - API changes, deprecations, migration requirements
7. **New releases** - Major version releases with architectural significance

## Secondary Topics

- Build tooling (osbuild, Containerfile-based OS)
- Container runtime integration (podman, quadlet, systemd-sysext)
- Kubernetes integration patterns
- Edge/IoT deployment patterns

## Skip

- Minor patch releases without notable changes
- User support questions
- Project-specific news without broader relevance
- Marketing announcements

## Output Format

## Executive Summary
3-4 sentences covering the most significant developments across the ecosystem.

## Cross-Project Trends
Patterns, convergences, or divergences worth noting across projects. Omit if none.

## Critical/Urgent
Security issues, breaking changes, or blockers. Omit if none.

## Project Updates

Group by project when there's significant activity:

### bootc / ostree
### Fedora Atomic
### Flatcar
### Talos
### Kairos

Only include sections with meaningful content.

## Technical Discussions
Design decisions, RFCs, and architectural threads worth following.

## Guidelines

- Highlight connections between projects (e.g., "Flatcar adopted X, similar to how CoreOS...")
- Lead with technical impact
- Include links to original sources
- Flag items requiring action or testing
- Omit empty sections

{errors_section}

Content to analyze:
{content}
