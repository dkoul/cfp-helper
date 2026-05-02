# CfP Helper

A Claude Code skill that acts as your Call for Papers (CfP) assistant for technical conferences. It helps you craft winning proposals, get honest feedback, and improve your submissions before the deadline.

## What It Does

CfP Helper provides three modes to help with conference submissions:

1. **idea2abstract** - Turn rough ideas into polished, submission-ready abstracts
2. **reviewer** - Get balanced, constructive feedback with pros/cons
3. **critic** - Receive tough, adversarial reviews to stress-test your proposal

The skill works with any technical conference by loading conference-specific rules and requirements.

## Quick Start

### Prerequisites

For dynamic CfP fetching (optional):
```bash
pip install requests beautifulsoup4
```

### Basic Usage

1. **Tell the skill which conference you're targeting:**
   - Name a conference: "Help me with KubeCon NA 2025"
   - Provide a CfP URL: "I want to submit to https://conf.example.com/cfp/"

2. **Choose your mode:**
   - "Turn my idea into an abstract"
   - "Review my proposal"
   - "Give me harsh criticism on this draft"

3. **Provide your content:**
   - For idea2abstract: Share your rough idea, bullet points, or topic
   - For reviewer/critic: Share your draft proposal

## The Three Modes

### Mode 1: idea2abstract

**When to use:** You have a rough idea but need help crafting a compelling abstract.

**What you get:**
- A submission-ready abstract with proper structure
- Title optimized for attention
- Suggested track and session type
- Character counts verified against conference limits
- Organizer notes with session outline

**Example request:**
```
I want to submit to KubeCon about using eBPF for observability.
My main idea is showing how we reduced observability costs by 70%
using custom eBPF programs instead of traditional agents.
```

### Mode 2: reviewer

**When to use:** You have a draft and want balanced, constructive feedback.

**What you get:**
- Scoring on 8 key criteria (originality, technical depth, etc.)
- Specific strengths highlighted
- Concerns that could hurt acceptance
- Actionable suggestions for improvement
- Verdict (Strong Accept → Reject)

**Example request:**
```
Review my DevConf proposal:

Title: Building Better CI/CD Pipelines
Abstract: In this talk, I'll share best practices for CI/CD...
```

### Mode 3: critic

**When to use:** You want brutal honesty to find every weakness before real reviewers do.

**What you get:**
- Adversarial review from a "harsh reviewer" persona
- Tests for novelty, depth, specificity, and vendor bias
- Direct identification of what's weak
- Concrete changes needed to earn an accept
- Competitive landscape analysis

**Example request:**
```
Be brutal with my proposal - I need to know if it's good enough.
[Your draft here]
```

## Working with Conferences

### Pre-configured Conferences

The `conferences/` directory contains pre-configured conference files:

- [kubecon-na-2025.md](conferences/kubecon-na-2025.md)
- [kubecon-na-2026.md](conferences/kubecon-na-2026.md)
- [devconfcz-2026.md](conferences/devconfcz-2026.md)
- [fossasia-2027.md](conferences/fossasia-2027.md)

### Adding a New Conference

#### Option 1: Dynamic Fetch (Quick)

Use the Python script to extract details from any CfP page:

```bash
# View details
python3 fetch_cfp.py https://conf.example.com/cfp/

# Save for reuse
python3 fetch_cfp.py --output conferences/myconf-2026.md \
  --format markdown https://conf.example.com/cfp/
```

**What it extracts:**
- Conference name, dates, location
- CfP deadlines
- Session types and durations
- Tracks/topics
- Character/word limits
- Speaker limits and requirements
- Review process information

**Limitations:**
- May miss JavaScript-rendered content
- Heuristic-based extraction may need manual review
- Always verify critical details (deadlines, limits)

#### Option 2: Manual File (Reusable)

Copy [conferences/_template.md](conferences/_template.md) and fill in the conference details:

```bash
cp conferences/_template.md conferences/myconf-2026.md
# Edit the file with conference details
```

## How It Works

1. **Loads conference rules** from `conferences/` or fetches dynamically
2. **Applies mode-specific logic:**
   - idea2abstract: Generates structured abstract following proven patterns
   - reviewer: Scores on rubric, provides balanced feedback
   - critic: Stress-tests with adversarial review
3. **Enforces constraints:**
   - Character/word limits
   - PII restrictions for blind reviews
   - Speaker limits
   - Conference-specific requirements

## Tips for Best Results

### For idea2abstract mode:
- Share as much context as you have (even if rough)
- Mention the specific problem you're solving
- Include any demos, data, or concrete examples
- Don't worry about formatting - just brain dump

### For reviewer mode:
- Provide the complete draft (title + abstract + extras)
- Include any additional fields (session type, track, etc.)
- Mention if you have specific concerns

### For critic mode:
- Use this when you think your proposal is ready
- Be prepared for blunt feedback
- Focus on the actionable suggestions, not the tone
- Run this before hitting submit

## Conference File Structure

Each conference file includes:

- Event details (dates, location, format)
- CfP timeline and deadlines
- Session types and durations
- Submission constraints (limits, speaker rules)
- Review criteria and what scores high
- Red flags to avoid
- Required fields beyond title/abstract
- Speaker benefits and requirements
- Conference-specific tips

See [conferences/_template.md](conferences/_template.md) for the full structure.

## Examples

### Example 1: Turning an Idea into an Abstract

**Input:**
```
Help me submit to KubeCon NA 2025. I want to talk about how we
built a platform that lets developers deploy preview environments
in under 30 seconds using Kubernetes and Argo.
```

**Output:**
- Hook that challenges current preview environment approaches
- Clear problem statement (slow, expensive preview envs)
- Specific promise (under 30s deploys, architecture explanation)
- Concrete takeaway (implementation blueprint)
- All within KubeCon's character limits and track alignment

### Example 2: Getting a Review

**Input:**
```
Review this for DevConf.cz 2026:

Title: Kubernetes Cost Optimization in Practice
Abstract: Learn how we reduced our Kubernetes costs by 60%...
```

**Output:**
- Rubric scores for all 8 criteria
- Strengths: Real metrics (60%), practical focus
- Concerns: Title is generic, needs more specificity
- Suggestions: Add specific techniques in title, mention tools used
- Verdict with justification

### Example 3: Adversarial Review

**Input:**
```
Give me brutal feedback on this proposal for FOSSASIA.
I need to know if it's actually good enough.
[Draft proposal]
```

**Output:**
- One-line takedown of biggest weakness
- Fair acknowledgment of what works
- Evidence-based criticisms (vague language, weak demo, generic content)
- Specific changes to earn an accept
- How it stacks up against likely competition

## Development

### File Structure
```
cfp-helper/
├── README.md              # This file
├── SKILL.md               # Skill instructions for Claude
├── fetch_cfp.py           # Dynamic CfP fetching script
└── conferences/
    ├── _template.md       # Template for new conferences
    ├── kubecon-na-2025.md
    ├── kubecon-na-2026.md
    ├── devconfcz-2026.md
    └── fossasia-2027.md
```

### Contributing Conference Files

To add a new conference:

1. Use `fetch_cfp.py` to extract basic details (if CfP page is available)
2. Copy `_template.md` and fill in the details
3. Include conference-specific quirks and tips
4. Verify all limits and requirements against the official CfP

## License

This skill is part of the Claude Code ecosystem and follows the same license terms.

## Support

For questions or issues with this skill, please open an issue in the Claude Code repository.
