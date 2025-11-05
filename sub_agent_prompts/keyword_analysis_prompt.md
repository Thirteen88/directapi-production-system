# Task Name: keyword_analysis

## Inputs
- topic: string (required) - The main topic or subject for keyword research
- target_audience: string (optional) - Description of the target audience demographics and interests
- industry: string (optional) - Industry or niche context for the keywords
- intent: string (optional) - Search intent type (informational, commercial, transactional, navigational)
- competitors: array[string] (optional) - List of competitor URLs or domains to analyze

## Constraints
- Token budget: 50000
- Data formats: JSON output only, structured keyword data with metrics
- Security constraints: Do not access external APIs or tools; base analysis on knowledge and patterns
- Scope: Focus on 15-30 primary keywords with variations
- Language: Default to English unless specified otherwise

## Success Criteria
- At least 15 relevant keywords identified with search intent classification
- Keywords categorized by difficulty (low, medium, high) and relevance score (1-10)
- Each keyword includes estimated search volume tier (low: <1k, medium: 1k-10k, high: >10k)
- Long-tail keyword variations provided for at least 50% of primary keywords
- Semantic keyword clusters identified showing topical relationships
- Clear rationale provided for each keyword's inclusion

## Output Format
JSON matching TaskOutput schema with:
- ok: boolean
- outputs: {
    primary_keywords: array[{
      keyword: string,
      search_intent: string,
      difficulty: string,
      relevance_score: number,
      volume_tier: string,
      variations: array[string]
    }],
    keyword_clusters: array[{
      cluster_name: string,
      keywords: array[string],
      topic_focus: string
    }],
    recommended_focus: array[string],
    competitive_gaps: array[string]
  }
- evidence: string (detailed analysis methodology and reasoning)
- provenance: { prompt_version: "1.0", inputs_hash, outputs_hash, delegation_timestamp }

## Execution Plan
Conduct comprehensive SEO keyword research by analyzing the provided topic and context to identify high-value search terms. Begin with seed keyword expansion, then classify by intent and difficulty. Group related keywords into semantic clusters to reveal content opportunities. Prioritize keywords that balance search volume potential with ranking feasibility. Identify competitive gaps where content could gain traction. Provide actionable recommendations with clear rationale for each keyword choice.

## Task Body

### Step 1: Seed Keyword Identification
- Analyze the provided topic to extract 5-10 core seed keywords
- Consider synonyms, related terms, and industry-specific terminology
- Document the reasoning for each seed keyword selection

### Step 2: Keyword Expansion
- For each seed keyword, generate 3-5 variations including:
  - Long-tail versions (3+ words)
  - Question-based formats (who, what, where, when, why, how)
  - Modifier combinations (best, top, guide, tips, vs, review)
- Consider user search patterns and natural language queries

### Step 3: Search Intent Classification
- Classify each keyword by primary search intent:
  - Informational: User seeking knowledge or answers
  - Commercial: User researching products/services before purchase
  - Transactional: User ready to take action or purchase
  - Navigational: User looking for specific website or brand
- Ensure diverse intent coverage across the keyword set

### Step 4: Difficulty and Relevance Assessment
- Assign difficulty level (low/medium/high) based on:
  - Keyword competitiveness in the industry
  - Likely domain authority of ranking pages
  - Specificity and niche nature of the term
- Assign relevance score (1-10) based on alignment with topic and target audience

### Step 5: Volume Tier Estimation
- Estimate search volume tier for each keyword:
  - Low: <1,000 monthly searches
  - Medium: 1,000-10,000 monthly searches
  - High: >10,000 monthly searches
- Base estimates on keyword specificity, industry size, and general search patterns

### Step 6: Semantic Clustering
- Group related keywords into 3-6 topical clusters
- Name each cluster based on the unifying theme
- Identify the primary topic focus for each cluster
- Ensure clusters align with potential content pillar structure

### Step 7: Competitive Gap Analysis
- Identify 5-10 keyword opportunities where:
  - Search demand exists but competition may be lower
  - Topic area is underserved in current content landscape
  - Long-tail variations offer ranking potential
- Highlight these as priority opportunities

### Step 8: Recommendation Synthesis
- Select 10-15 recommended focus keywords based on:
  - Balance of difficulty vs. opportunity
  - Intent diversity
  - Cluster coverage
- Provide clear rationale for each recommendation

### Step 9: Evidence Documentation
- Compile detailed evidence string explaining:
  - Research methodology applied
  - Key patterns observed
  - Assumptions made in volume/difficulty estimates
  - Strategic reasoning for recommendations

### Step 10: Output Validation
- Verify all required output fields are populated
- Ensure JSON structure matches schema exactly
- Confirm provenance data is complete and accurate
- Set ok: true if all success criteria met, false otherwise
