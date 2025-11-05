# Task Name: outline_generation

## Inputs
- topic: string (required) - The main topic or title for the content piece
- keywords: array[string] (required) - Primary keywords to incorporate into the outline
- target_word_count: number (optional) - Desired total word count (default: 2000)
- content_type: string (optional) - Type of content (blog_post, guide, tutorial, listicle, comparison, case_study)
- target_audience: string (optional) - Description of intended readers and their expertise level
- tone: string (optional) - Desired tone (professional, conversational, technical, friendly)
- key_points: array[string] (optional) - Specific points or subtopics that must be covered

## Constraints
- Token budget: 40000
- Data formats: JSON output with structured hierarchical outline
- Security constraints: Content must be appropriate and factual; avoid controversial or sensitive topics without proper framing
- Scope: Outline should include 5-10 main sections with 2-5 subsections each
- Structure depth: Maximum 3 levels (H2, H3, H4)

## Success Criteria
- Logical content flow with clear introduction, body, and conclusion
- All provided keywords naturally integrated into section headings where appropriate
- Each section includes purpose statement and estimated word count
- Total estimated word count within 10% of target (if provided)
- Subsections support parent sections coherently
- Content type best practices followed (e.g., listicles have numbered items)
- At least one call-to-action or engagement point identified
- Outline enables comprehensive coverage of the topic without redundancy

## Output Format
JSON matching TaskOutput schema with:
- ok: boolean
- outputs: {
    title: string,
    meta_description: string,
    introduction: {
      hook: string,
      key_points: array[string],
      word_count: number
    },
    sections: array[{
      heading: string,
      level: number,
      purpose: string,
      word_count: number,
      keywords_targeted: array[string],
      subsections: array[{
        heading: string,
        level: number,
        purpose: string,
        word_count: number
      }]
    }],
    conclusion: {
      summary_points: array[string],
      call_to_action: string,
      word_count: number
    },
    total_estimated_words: number,
    seo_notes: string
  }
- evidence: string (explanation of structural decisions and keyword integration strategy)
- provenance: { prompt_version: "1.0", inputs_hash, outputs_hash, delegation_timestamp }

## Execution Plan
Generate a comprehensive, SEO-optimized content outline that provides clear structure and direction for content creation. Begin by analyzing the topic and keywords to determine optimal content angle and structure. Design a logical flow that guides readers from introduction through key concepts to actionable conclusion. Integrate keywords naturally into headings while maintaining readability. Allocate word counts strategically to ensure depth where needed. Include meta-description and SEO guidance to maximize search visibility. Ensure the outline enables a writer to produce high-quality, comprehensive content efficiently.

## Task Body

### Step 1: Topic Analysis and Angle Definition
- Analyze the provided topic to identify the core value proposition
- Review keywords to understand search intent and user expectations
- Determine the most compelling content angle based on:
  - Keyword intent (informational, commercial, etc.)
  - Content type specifications
  - Target audience needs
- Define the unique perspective or approach this content will take

### Step 2: Title Optimization
- Craft a compelling title that:
  - Incorporates the primary keyword naturally
  - Clearly communicates the content value
  - Includes power words or numbers if appropriate for content type
  - Stays within 50-60 characters for SEO
- Ensure title matches content type conventions (e.g., "10 Ways to..." for listicles)

### Step 3: Meta Description Creation
- Write a 150-160 character meta description that:
  - Summarizes the content value proposition
  - Includes primary keyword
  - Encourages click-through with action words
  - Sets accurate expectations for content

### Step 4: Introduction Planning
- Design introduction structure (150-250 words):
  - Hook: Opening sentence that captures attention
  - Key points: 3-5 bullet points previewing main takeaways
  - Purpose: What readers will learn or achieve
- Ensure introduction incorporates primary keyword within first 100 words

### Step 5: Main Section Architecture
- Create 5-10 main sections (H2 level) that:
  - Follow logical progression or narrative flow
  - Each addresses a distinct aspect of the topic
  - Build upon each other when appropriate
  - Incorporate keywords into 60-70% of headings naturally
- For each section, define:
  - Clear purpose statement (what this section accomplishes)
  - Estimated word count (proportional to importance)
  - Target keywords to integrate

### Step 6: Subsection Development
- For each main section, create 2-5 subsections (H3 level):
  - Break down complex topics into digestible parts
  - Maintain parallel structure within each section
  - Include specific, actionable headings
  - Add H4 subsections only when absolutely necessary for clarity
- Assign word counts to subsections based on depth needed

### Step 7: Content Type Optimization
- Apply content type-specific best practices:
  - **Blog Post**: Conversational flow, storytelling elements
  - **Guide**: Comprehensive coverage, step-by-step structure
  - **Tutorial**: Sequential instructions, clear action items
  - **Listicle**: Numbered items, consistent formatting
  - **Comparison**: Side-by-side analysis, pros/cons
  - **Case Study**: Problem-solution-results structure

### Step 8: Conclusion Design
- Structure conclusion (150-200 words):
  - Summary points: 3-5 key takeaways
  - Call-to-action: Specific next step for readers
  - Final thought: Memorable closing statement
- Reinforce primary keyword once more

### Step 9: Word Count Validation
- Calculate total estimated word count across all sections
- Verify total is within 10% of target word count
- Adjust section allocations if necessary
- Ensure proper distribution: 10% intro, 80% body, 10% conclusion

### Step 10: SEO Notes Compilation
- Document SEO considerations:
  - Keyword placement strategy
  - Internal linking opportunities
  - Image/media recommendations
  - Featured snippet optimization potential
  - Related keywords to naturally incorporate in body

### Step 11: Quality Review
- Verify outline coherence and logical flow
- Check for keyword stuffing or unnatural integration
- Ensure all required key_points (if provided) are covered
- Confirm outline enables comprehensive topic coverage
- Validate that structure supports target audience's expertise level

### Step 12: Evidence Documentation
- Compile evidence string explaining:
  - Structural decisions and rationale
  - Keyword integration strategy
  - Content type adaptations applied
  - Word count allocation reasoning

### Step 13: Output Validation
- Verify all required output fields are populated correctly
- Ensure JSON structure matches schema exactly
- Confirm provenance data is complete and accurate
- Set ok: true if all success criteria met, false otherwise
