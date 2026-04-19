# Implicit Defaults: A Pilot Study on Demographic Bias in AI Image Generation

*Draft — work in progress*

---

## Abstract

*(To be written once results section is complete.)*

AI image generation models have become widely used tools for creating visual content, yet the demographic assumptions embedded in these models are rarely transparent or examined. This pilot study investigates what happens when demographic attributes are omitted from prompts: which defaults does each model apply silently? We compare the perceived demographic distribution of AI-generated images against reference images from internet search engines and stock photography, and contextualise these against real-world population statistics. Our goal is not to prescribe what AI should generate, but to raise awareness that unspecified prompts silently inherit model-specific biases that are neither documented nor well-studied.

---

## 1. Introduction

When a user prompts an AI image generation model with "a person" or "a CEO", the model must implicitly decide what that person looks like. These decisions — perceived gender, perceived ancestry, age, skin tone — are not random. They reflect patterns learned from training data and design choices made during model development, and they are largely invisible to the user.

This matters in practice. A designer generating placeholder portraits, a researcher illustrating a report, or a developer testing a UI will receive images shaped by these defaults without necessarily realising it. The resulting content may reinforce stereotypes or systematically under-represent large parts of the world population.

This paper makes no normative claims about what AI image generators *should* produce. Instead, it asks a descriptive question: **what do they actually produce by default, and how does that compare to internet image search results and real-world demographics?**

We frame this as a three-layer comparison:

1. **Real-world baseline** — population statistics (e.g. world population by region for "Person"; labour force statistics for occupational prompts)
2. **Internet representation** — what Google Image Search and Adobe Stock return for the same prompt
3. **AI generation** — what leading generative models produce for the same prompt

Each layer can introduce or amplify demographic skew. By making all three visible in one study, we aim to illustrate where bias enters the pipeline and to what degree.

This is an exploratory pilot study. All results are based on small samples (n=24 per source) and should be interpreted as illustrative rather than statistically definitive. However, as we argue in Section 5, strong distributional skews at small sample sizes are informative: a 23/24 result does not become meaningfully different at n=1000.

---

## 2. Related Work

*(To be expanded.)*

- **Gender Shades** (Buolamwini & Gebru, 2018) — audit of facial recognition systems; introduced the "perceived" framing for demographic attributes assessed from visual appearance
- Audit studies of text-to-image models (e.g. Bianchi et al., 2023 — "Easily Accessible Text-to-Image Generation Amplifies Demographic Stereotypes at Large Scale")
- Studies on occupational bias in image search (e.g. Kay et al., 2015 — "Unequal Representation and Gender Stereotypes in Image Search Results")
- *(Add further references as the paper develops)*

---

## 3. Methodology

### 3.1 Prompt design

All images were collected or generated using a single neutral prompt per category. For this pilot, the prompt is **"Person"** — intentionally generic to surface default assumptions with no occupational or contextual framing.

### 3.2 Image sources

Seven sources were used, divided into two groups:

**Reference sources (internet imagery):**
- Google Image Search (first 24 results)
- Adobe Stock (first 24 results)

**AI generative sources:**
- FLUX
- FLUX2
- NanoBanana
- Qwen
- Sora

Each source contributes 24 images, for a total of 168 images in this pilot.

### 3.3 Attribute labeling

Each image was labeled by a GPT-4o vision model using a structured prompt (see `Generate_Image_Labels_Prompt.txt`). Labels capture the following attributes based solely on visual appearance:

| Attribute | Type | Notes |
|---|---|---|
| `perceived_gender` | categorical | Based on visual presentation only |
| `perceived_ancestry_cluster` | categorical | Broad regional clusters; perceived, not genetic |
| `age_estimate` | integer | Approximate age in years |
| `skin_tone` | categorical | light / medium / brown / dark |
| `eye_color` | categorical | |
| `hair_color` | categorical | |
| `glasses` | boolean | |
| `beard_style` | categorical | |

All attributes involving sensitive characteristics are explicitly framed as *perceived* — i.e. what is visually presented in the image — following the convention established by Buolamwini & Gebru (2018). No claims are made about the actual identity of any depicted person.

The labeling model was instructed to use `"unknown"` only when an image was genuinely too ambiguous or low-quality to make a reasonable visual assessment.

### 3.4 Real-world baseline

Where available, we compare AI-generated distributions against the best publicly available global statistics. These baselines are used descriptively — not to argue that AI *should* match them, but to make the magnitude of any deviation visible.

#### Gender

The global sex ratio is approximately 50.3% male / 49.7% female (World Bank, 2024 [@worldbank_gender]; UN WPP 2024 [@un_wpp2024]).

#### Age

According to the UN World Population Prospects 2024 [@un_wpp2024]:

| Age group | World population share (approx.) |
|---|---|
| 0–14 years | ~25% |
| 15–29 years | ~24% |
| 30–44 years | ~21% |
| 45–59 years | ~17% |
| 60+ years | ~13% |

Global median age is approximately 30 years, with significant regional variation (Sub-Saharan Africa ~18 years; Europe ~43 years).

#### Perceived ancestry / skin tone

Global population distribution by ancestry is approximated using broad geographic region shares (UN WPP 2024 [@un_wpp2024]):

| Region | World population share (approx.) |
|---|---|
| South, Southeast & East Asia | ~55% |
| Sub-Saharan Africa | ~15% |
| West Eurasia / Europe / MENA | ~20% |
| Americas | ~8% |
| Other | ~2% |

For skin tone specifically, a comparable global baseline could not be identified in the literature. Global skin tone statistics appear to be sparse and methodologically contested — the Fitzpatrick scale [@fitzpatrick1988skin], while widely used clinically, is noted to be Eurocentric and insufficient for capturing the full global spectrum of skin pigmentation [@quillen2019skincolor; @jablonski2010skincolor]. Skin tone results in this study are therefore presented descriptively, without comparison to a real-world reference. We use the four-level scale (*light, medium, brown, dark*) derived from visual labeling rather than the Fitzpatrick classification.

#### Eye color

Global eye color distribution is heavily skewed toward brown, which predominates across Africa, Asia, and Latin America. Estimates from large genome-wide association studies [@simcoe2021eyecolor]:

| Eye color | Global share (approx.) |
|---|---|
| Brown | ~70–80% |
| Blue | ~8–10% |
| Hazel | ~5% |
| Amber | ~5% |
| Grey | ~3% |
| Green | ~2% |

#### Hair color

Black hair is by far the most common globally, reflecting the large populations of Asia, Africa, and Latin America. Estimates derived from genetic and demographic studies [@hysi2021haircolor; @morgan2018haircolor]:

| Hair color | Global share (approx.) |
|---|---|
| Black | ~75–85% |
| Brown | ~11% |
| Blonde | ~2% |
| Red | ~1–2% |
| White / grey | age-dependent |

**Important caveat:** precise global percentages for hair color, eye color, and skin tone are not available from a single authoritative source. The figures above are approximations derived from genetic studies (predominantly conducted on European-ancestry cohorts) and regional demographic data. They should be treated as indicative rather than definitive.

#### Occupational prompts (future extension)

For occupational prompts (CEO, Doctor, Housekeeper, etc.), ILO labour force statistics will be used as the real-world baseline where available.

### 3.5 Limitations

- Sample size of n=24 per source is small. Results are illustrative; individual images can shift percentages by ~4 percentage points.
- Internet search results vary over time and by region/language of the search. Searches were conducted from a single location.
- GPT-4o labeling introduces its own potential biases. The labeling model may itself reflect training data skews in how it perceives ancestry or gender.
- The set of AI models included is not exhaustive.

---

## 4. Results

*(Charts are generated by `paper/generate_figures.py` from `statistics.json`.)*

### 4.1 Perceived gender

![Perceived gender distribution by source](figures/gender_by_source.png)

*(Key finding to be written. Preliminary: female 54%, male 46% overall, but with notable variation across sources.)*

### 4.2 Perceived ancestry cluster

![Perceived ancestry cluster by source](figures/ancestry_by_source.png)

*(Key finding to be written. Preliminary: West Eurasian = 70% overall across all sources, Sub-Saharan African = 15%, East Asian = 13%, South Asian = 1%.)*

### 4.3 Skin tone

![Skin tone distribution by source](figures/skin_tone_by_source.png)

*(Key finding to be written. Preliminary: light skin tone = 77% overall.)*

### 4.4 Age distribution

![Age estimate distribution by source](figures/age_by_source.png)

*(Key finding to be written.)*

### 4.5 Inter-model variation

*(Compare AI sources against each other: do they agree, or do individual models show stronger skews?)*

### 4.6 Intersectionality

*(Do gender and ancestry cluster interact? E.g. does a particular model skew toward a specific gender–ancestry combination?)*

---

## 5. Discussion

### 5.1 The three-layer framing

*(Discuss drift across layers: does AI amplify internet bias? Does internet imagery already diverge from world population? Where is the largest gap?)*

### 5.2 Invisible defaults

The central practical takeaway is that omitting demographic attributes from prompts does not produce neutral output — it produces *default* output shaped by the model's training data. Users who are unaware of this may inadvertently produce demographically skewed content. Making these defaults visible is a prerequisite for making informed decisions about when and how to specify attributes explicitly.

### 5.3 Implications for prompt design

*(Brief practical guidance: explicitly specifying attributes gives predictable results; relying on defaults does not.)*

---

## 6. Conclusion

*(To be written once results are complete.)*

---

## References

*(See `references.bib`.)*

---

*Appendix: Labeling prompt used for GPT-4o attribute extraction — see `Generate_Image_Labels_Prompt.txt` in the repository root.*
