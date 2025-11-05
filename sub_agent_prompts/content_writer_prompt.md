# Task Name: content_writer

## Inputs
- outline: object (required) - Complete outline structure from outline_generation task
- keywords: array[string] (required) - Primary and secondary keywords to incorporate
- tone: string (optional) - Writing tone (professional, conversational, technical, friendly, authoritative)
- target_audience: string (optional) - Description of intended readers and expertise level
- style_guidelines: object (optional) - Specific style rules { sentence_length, paragraph_length, active_voice_percentage, readability_grade }
- brand_voice: string (optional) - Brand-specific voice characteristics and preferences
- citations_required: boolean (optional) - Whether to include reference placeholders for factual claims
- include_examples: boolean (optional) - Whether to include practical examples and use cases

## Constraints
- Token budget: 100000
- Data formats: JSON output with structured content sections and markdown formatting
- Security constraints: Generate original content; do not reproduce copyrighted material; maintain factual accuracy
- Quality standards: Readability grade 8-10, active voice 70%+, varied sentence structure
- Keyword density: 1-2% for primary keyword, natural integration of secondary keywords
- Scope: Generate complete content matching outline word count targets (±5%)

## Success Criteria
- All outline sections fully developed with engaging, well-written content
- Target word count achieved within 5% variance per section
- Keywords integrated naturally without keyword stuffing (density check passed)
- Tone and style consistent throughout content
- Readability score appropriate for target audience (Flesch-Kincaid 50-70)
- Clear topic sentences and logical paragraph transitions
- Introduction includes compelling hook and value proposition
- Conclusion includes actionable takeaways and call-to-action
- Content is factually coherent and valuable to readers
- No placeholder text or incomplete sections remain

## Output Format
JSON matching TaskOutput schema with:
- ok: boolean
- outputs: {
    title: string,
    meta_description: string,
    content_sections: array[{
      heading: string,
      level: number,
      content: string,
      word_count: number,
      keywords_used: array[string]
    }],
    full_content_markdown: string,
    content_statistics: {
      total_words: number,
      total_paragraphs: number,
      total_sentences: number,
      avg_sentence_length: number,
      readability_score: number,
      keyword_density: object
    },
    seo_elements: {
      h1: string,
      h2_tags: array[string],
      keyword_positions: array[number],
      internal_link_suggestions: array[string]
    },
    quality_checks: {
      tone_consistency: boolean,
      active_voice_percentage: number,
      unique_value_delivered: boolean
    }
  }
- evidence: string (detailed explanation of writing approach, keyword integration, and quality assurance)
- provenance: { prompt_version: "1.0", inputs_hash, outputs_hash, delegation_timestamp }

## Execution Plan
Generate high-quality, SEO-optimized content based on the provided outline structure. Begin by establishing the appropriate tone and style for the target audience. Write each section methodically, ensuring engaging prose that naturally incorporates keywords while maintaining readability and value. Use varied sentence structures, clear topic sentences, and smooth transitions between ideas. Include practical examples and actionable insights where appropriate. Conduct quality checks on readability, keyword density, and tone consistency. Deliver polished, publication-ready content that ranks well and serves reader needs.

## Task Body

### Step 1: Voice and Style Calibration
- Analyze tone, target_audience, and brand_voice inputs
- Establish writing voice parameters:
  - Formality level (casual to formal)
  - Technical depth (beginner to expert)
  - Perspective (second person "you" vs third person)
  - Personality traits (authoritative, friendly, empathetic)
- Review style_guidelines for specific constraints
- Set internal quality targets for this content piece

### Step 2: Introduction Writing
- Craft compelling hook (first sentence) that:
  - Captures attention immediately
  - Relates to reader's pain point or interest
  - Sets up the value proposition
- Expand introduction following outline structure:
  - Establish context and relevance
  - Preview key takeaways
  - Integrate primary keyword naturally within first 100 words
  - Create smooth transition to first main section
- Target word count: Match outline specification (typically 150-250 words)

### Step 3: Main Content Development - Section by Section
For each main section in the outline:

**3a. Section Opening**
- Write strong topic sentence that introduces section focus
- Connect to previous section when appropriate
- Integrate section keyword naturally in opening paragraph

**3b. Content Expansion**
- Develop subsections according to outline structure
- For each paragraph:
  - Start with clear topic sentence
  - Support with explanations, examples, or evidence
  - Maintain 3-5 sentences per paragraph average
  - Use transitional phrases between paragraphs
- Vary sentence structure: mix short punchy sentences with longer complex ones
- Aim for 70%+ active voice construction

**3c. Examples and Evidence**
- Include practical examples when include_examples is true
- Add specific, concrete details rather than vague generalizations
- Use scenarios, case studies, or data points where relevant
- If citations_required is true, add [Citation needed: topic] placeholders

**3d. Keyword Integration**
- Incorporate relevant keywords from the keywords array naturally
- Use semantic variations and related terms
- Avoid forced or repetitive keyword usage
- Track keyword placement for density monitoring

**3e. Engagement Elements**
- Add rhetorical questions to engage readers
- Use bullet points or numbered lists for scanability
- Include bolded key phrases for emphasis (sparingly)
- Break up text with subheadings as per outline

**3f. Word Count Management**
- Monitor word count per section against outline targets
- Adjust depth and detail to meet targets within ±5%
- Ensure proportional development across sections

### Step 4: Conclusion Writing
- Summarize key takeaways (3-5 main points)
- Reinforce the value delivered to the reader
- Include clear call-to-action from outline
- End with memorable final thought or question
- Integrate primary keyword one final time naturally
- Target word count: Match outline specification (typically 150-200 words)

### Step 5: Content Assembly
- Compile all sections into full_content_markdown format
- Apply proper markdown formatting:
  - # for H1 (title only)
  - ## for H2 (main sections)
  - ### for H3 (subsections)
  - #### for H4 (if used)
  - **bold** for emphasis
  - - or 1. for lists
- Ensure proper spacing and formatting consistency

### Step 6: SEO Element Extraction
- Extract H1 tag (title)
- Compile array of all H2 tags used
- Document keyword positions (paragraph numbers where keywords appear)
- Generate 5-10 internal_link_suggestions based on:
  - Related topics mentioned
  - Natural anchor text opportunities
  - Supporting content needs

### Step 7: Content Statistics Calculation
- Count total words across all sections
- Count total paragraphs and sentences
- Calculate average sentence length (words per sentence)
- Estimate readability score using Flesch-Kincaid approximation:
  - Score 60-70: Plain English, easily understood
  - Score 50-60: Fairly difficult, 10th-12th grade
  - Score 30-50: Difficult, college level
- Calculate keyword density for each target keyword:
  - Primary keyword: Target 1-2%
  - Secondary keywords: Track frequency

### Step 8: Quality Assurance Checks
**Tone Consistency Review**
- Scan content for tone shifts or inconsistencies
- Verify voice matches established parameters
- Check that formality level is maintained throughout
- Set tone_consistency: true if consistent, false if issues detected

**Active Voice Analysis**
- Sample 20-30 sentences across content
- Identify passive voice constructions
- Calculate approximate active_voice_percentage
- Target: 70% or higher

**Value Delivery Assessment**
- Evaluate whether content provides unique insights
- Verify actionable takeaways are present
- Confirm reader questions would be answered
- Set unique_value_delivered based on assessment

**Readability Review**
- Check for overly complex sentences (>30 words)
- Verify paragraph length variety (avoid walls of text)
- Ensure transitions flow naturally
- Confirm scanability with subheadings and lists

**Keyword Optimization Review**
- Verify primary keyword appears in:
  - Title
  - First 100 words
  - At least one H2 heading
  - Conclusion
- Check that keyword density is within 1-2% range
- Ensure keywords appear natural, not forced

### Step 9: Content Refinement
Based on quality checks:
- Revise any sections with tone inconsistencies
- Convert passive voice to active where possible
- Break up overly long sentences or paragraphs
- Add transitions where flow is abrupt
- Adjust keyword usage if density is too high or too low
- Enhance examples or details if value seems thin

### Step 10: Final Polish
- Proofread for grammar and spelling
- Check capitalization consistency
- Verify markdown formatting correctness
- Ensure all outline sections are fully developed
- Confirm no placeholder or incomplete content remains

### Step 11: Evidence Documentation
- Compile detailed evidence string covering:
  - Writing approach and tone decisions
  - Keyword integration strategy and placement
  - Quality assurance results and adjustments made
  - Content value proposition and unique angles
  - Any challenges encountered and how resolved

### Step 12: Output Validation
- Verify all required output fields are populated
- Ensure content_sections array matches outline structure
- Confirm full_content_markdown is complete and properly formatted
- Validate content_statistics calculations
- Check that seo_elements are accurately extracted
- Verify quality_checks reflect actual content characteristics
- Ensure JSON structure matches schema exactly
- Confirm provenance data is complete and accurate
- Set ok: true if all success criteria met, false otherwise
