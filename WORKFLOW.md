# Review Workflow

## Roles

### Reviewer (2 required)
- Reviews all papers
- Decisions: Keep, Reject, or Flag for Systems
- Can flag papers that need technical review

### Moderator (1)
- Resolves disputes when reviewers disagree (1 Keep, 1 Reject)
- Does NOT see papers with 2-2 agreement or flagged papers

### Systems Reviewer (1)
- Reviews ONLY flagged papers
- Technical review for edge cases

### Supervisor (view-only)
- Views consensus results
- Exports final paper list to CSV
- Monitors team progress

### Admin
- Full access to all features
- User management

## Consensus Logic

### Automatic Consensus
- **2 Keep votes** → Paper approved automatically
- **2 Reject votes** → Paper rejected automatically

### Moderator Review
- **1 Keep + 1 Reject** → Goes to Moderator
- Moderator decision is final
- Moderator Keep → Adds to consensus
- Moderator Reject → Excluded from consensus

### Systems Review
- **Any Flag** → Bypasses moderator, goes to Systems
- Can be flagged by either reviewer
- Systems Keep → Adds to consensus
- Systems Reject → Excluded from consensus

### Final Consensus
Papers approved through:
1. 2 Reviewer Keep votes (not flagged)
2. Moderator Keep decision
3. Systems Keep decision

## User Interface

### Reviewer Interface
- Swipe right or press `Y` = Keep
- Swipe left or press `N` = Reject
- Click Flag button = Send to Systems
- Shows title, authors, year only (no abstract)
- Progress bar and stats

### Moderator Interface
- Shows only disputed papers (1 Keep, 1 Reject)
- Displays vote counts
- Same swipe mechanics as reviewers
- Stats: Pending/Completed

### Systems Interface
- Shows only flagged papers
- Displays who flagged it
- Same swipe mechanics
- Stats: Total Flagged/Pending/Reviewed

### Supervisor Interface
- Read-only dashboard
- List of all consensus papers
- Progress statistics
- Export to CSV button
- Auto-refreshes every 30 seconds

## Registration

### Creating Accounts

1. Go to `/signup`
2. Enter username and password
3. Use invite code from `server/config.py`
4. Account role determined by invite code

### Invite Codes (Default)
```python
'HERO-REVIEWER1-2025': {'role': 'reviewer'}
'HERO-REVIEWER2-2025': {'role': 'reviewer'}
'HERO-MODERATOR-2025': {'role': 'moderator'}
'HERO-SYSTEMS-2025': {'role': 'systems'}
'HERO-SUPERVISOR-2025': {'role': 'supervisor'}
'HERO-ADMIN-2025': {'role': 'admin'}
```

Update in `server/config.py` before deployment.

## Workflow Example

### Scenario 1: Agreement
1. Reviewer 1: Keep
2. Reviewer 2: Keep
3. **Result:** Paper automatically in consensus ✓

### Scenario 2: Disagreement
1. Reviewer 1: Keep
2. Reviewer 2: Reject
3. Moderator reviews → Keep
4. **Result:** Paper in consensus ✓

### Scenario 3: Flagged Paper
1. Reviewer 1: Keep + Flag
2. Reviewer 2: (doesn't see it yet)
3. Systems reviews → Keep
4. **Result:** Paper in consensus ✓

### Scenario 4: Rejection
1. Reviewer 1: Reject
2. Reviewer 2: Reject
3. **Result:** Paper automatically rejected ✗

## Progress Tracking

### Individual Progress
- Current paper index
- Total kept
- Total rejected
- Completion percentage

### Team Progress (Supervisor)
- Total papers reviewed
- Consensus count
- Pending moderator decisions
- Pending systems reviews

## Export

Supervisor can export consensus papers to CSV:
- Title
- Authors
- Year
- DOI
- Source
- Decision Type (Reviewer Consensus / Moderator / Systems)

## Best Practices

1. **Reviewers:** Focus on title/authors/year only for unbiased initial screening
2. **Flag liberally:** When in doubt, flag for systems review
3. **Moderator:** Break ties quickly to maintain workflow momentum
4. **Systems:** Deep dive on technical merit of flagged papers
5. **Supervisor:** Monitor progress regularly, export incrementally