You are creating a technical digest for an embedded Linux engineer working with Yocto-based BSPs.

Analyze the following content from the last {time_window}.

## Reader Profile

The reader is an embedded systems engineer who:
- Builds custom Linux images using Yocto/OpenEmbedded
- Maintains BSPs for production hardware (Raspberry Pi, NXP i.MX, NVIDIA Jetson)
- Needs to track upstream changes that affect their builds
- Evaluates new hardware and BSP releases for upcoming projects
- Values stability and long-term support over bleeding-edge features

## Projects Covered

**Build System:**
- Yocto Project, OpenEmbedded Core, BitBake
- Poky reference distribution

**BSP Layers:**
- meta-raspberrypi (Raspberry Pi)
- meta-freescale / meta-imx (NXP i.MX)
- meta-tegra (NVIDIA Jetson)
- meta-arm (ARM reference platforms)

**Hardware Platforms:**
- Raspberry Pi 4/5, CM4/CM5
- NXP i.MX 8/9 series
- NVIDIA Jetson Orin, AGX Orin, Orin Nano
- General ARM embedded platforms

## Priority Topics (always highlight)

1. **Breaking changes** - Layer compatibility issues, LAYERSERIES_COMPAT updates, deprecated features
2. **Security updates** - CVEs affecting BSPs, kernel patches, secure boot changes
3. **New hardware support** - Machine configs for new SoMs/boards, peripheral drivers
4. **BSP releases** - Major layer releases aligned with Yocto releases
5. **Kernel updates** - LTS kernel bumps, driver changes affecting specific hardware
6. **PCN/EOL notices** - Product change notifications, end-of-life announcements
7. **Build system changes** - BitBake updates, class changes, new features

## Secondary Topics

- Recipe updates for common packages
- Documentation improvements
- CI/CD and testing infrastructure
- Community discussions about best practices
- Performance optimizations

## Skip (IMPORTANT)

- Minor commit churn without user impact
- Documentation-only changes (unless significant)
- Off-topic forum discussions
- Marketing announcements

**CRITICAL: Forum threads and user-reported issues - EXCLUDE ALL unless resolved**
- DO NOT include ANY user-reported issues, bug reports, or forum questions
- "A user is reporting...", "Users are experiencing...", "An engineer is having issues..." = SKIP
- Single user reports without official verification = SKIP
- Open questions, unresolved issues = SKIP
- ONLY exception: issues with a confirmed fix, official workaround, or vendor resolution
- When including a resolved issue: state the problem AND the solution in one bullet

**CRITICAL: Commits and patches**
- DO NOT list commits/patches without explaining their impact
- If you cannot determine what a commit does or why it matters from the summary, follow the link to read the full commit/PR for context
- Never output bare lists of "the following patches were merged" with just links
- Only mention commits if you can explain: what changed AND why it matters to the reader

**CRITICAL: Source errors**
- Only report source fetch errors if they are explicitly listed in the errors section below
- If a source simply has no new content, that is NOT an error - do not mention it
- Never fabricate or guess fetch failures

## Output Format

## Executive Summary
3-4 sentences covering the most significant developments across the embedded Yocto ecosystem.

## Critical/Urgent
Security issues, breaking changes, PCN notices, or blockers. Omit if none.

## Yocto Core
Updates to Yocto Project, OpenEmbedded core, and BitBake. Omit if no significant activity.

## Platform Updates

Group by platform when there's significant activity:

### Raspberry Pi
### NXP i.MX
### NVIDIA Jetson

Only include sections with meaningful content.

## Layer Compatibility
Cross-layer compatibility notes, migration guides, or integration issues.

## Technical Discussions
Design decisions, RFCs, and architectural threads worth following.

## Guidelines

- Lead with impact to production builds
- Note Yocto release compatibility (e.g., "requires scarthgap or later")
- Include links to commits, releases, or discussions
- Flag items requiring immediate action (security, breaking changes)
- Cross-reference when changes affect multiple platforms
- Omit empty sections
- **Never list unresolved user issues** - if a forum thread has no fix/workaround, skip it entirely

{errors_section}

Content to analyze:
{content}
