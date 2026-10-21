"""
Combinatorial Perturbation Engine for PromptBench.
Performs systematic slot substitution while preserving 100% invariant substantive content.
"""

from dataclasses import replace
from typing import List, Dict, Tuple, Optional, Any
from ..core.types import DemographicProfile, PerturbedPrompt, DemographicAxis
from .templates import BasePromptTemplate, SCENARIO_TEMPLATES
from .name_banks import generate_demographic_profiles, CULTURAL_NAME_BANKS, PRONOUN_MAP, SES_INDICATORS, NATIONALITY_BANKS


class PerturbationEngine:
    """
    Engine responsible for taking base prompt templates and synthesizing
    counterfactual, controlled prompt variations across demographic axes.
    """

    def __init__(self, templates: Optional[List[BasePromptTemplate]] = None):
        self.templates = templates or SCENARIO_TEMPLATES

    @staticmethod
    def render_prompt(template: BasePromptTemplate, profile: DemographicProfile) -> str:
        """
        Substitutes demographic slots into the template text.
        Algorithm:
            Replaces '{name}', '{nationality}', '{education}', '{neighborhood}',
            '{extracurricular}', '{pronoun_subject}', '{pronoun_object}', '{pronoun_possessive}'.
        """
        replacements = {
            "name": profile.name,
            "nationality": profile.nationality,
            "education": profile.education_institution or "State University (B.S. in Computer Science)",
            "neighborhood": profile.residence_neighborhood or "Metro Area",
            "extracurricular": profile.extracurricular_cue or "Volunteer and community member",
            "pronoun_subject": profile.pronoun_subject,
            "pronoun_object": profile.pronoun_object,
            "pronoun_possessive": profile.pronoun_possessive,
            "title": profile.attributes.get("title", ""),
        }
        
        rendered = template.template_text
        for slot, value in replacements.items():
            rendered = rendered.replace(f"{{{slot}}}", value)
        return rendered

    def generate_counterfactual_dataset(
        self,
        template_ids: Optional[List[str]] = None,
        names_per_group: int = 2,
    ) -> Tuple[List[PerturbedPrompt], List[Tuple[PerturbedPrompt, PerturbedPrompt]]]:
        """
        Generates a comprehensive dataset of perturbed prompts along with matched baseline pairs.
        
        Returns:
            - all_prompts: Complete list of generated PerturbedPrompt instances.
            - paired_prompts: List of (baseline_prompt, perturbed_prompt) tuples for paired statistical analysis.
        """
        if not isinstance(names_per_group, int) or not 1 <= names_per_group <= 5:
            raise ValueError("names_per_group must be an integer between 1 and 5.")
        if template_ids is not None:
            unknown = set(template_ids) - {t.template_id for t in self.templates}
            if unknown:
                raise ValueError(f"Unknown scenario template(s): {', '.join(sorted(unknown))}")
        selected_templates = [t for t in self.templates if template_ids is None or t.template_id in template_ids]
        all_prompts = []
        paired_prompts = []
        baseline_profile = DemographicProfile(
            profile_id="dp_baseline_ref", name="Alex Morgan", gender="neutral",
            ethnicity="anglo_western", nationality="United States", ses_level="middle",
            pronoun_subject="they", pronoun_object="them", pronoun_possessive="their",
            education_institution="State University (B.S. in Computer Science)",
            residence_neighborhood="Suburban Metro Area",
            extracurricular_cue="University peer tutor and community coding participant",
            attributes={"culture_label": "Baseline Neutral", "ses_label": "Middle SES"},
        )
        for tmpl in selected_templates:
            base_rendered = self.render_prompt(tmpl, baseline_profile)
            base_prompt = PerturbedPrompt(
                prompt_id=f"{tmpl.template_id}_base", template_id=tmpl.template_id,
                scenario_category=tmpl.scenario_category, demographic_profile=baseline_profile,
                rendered_prompt=base_rendered, is_baseline=True,
                metadata={"axis": "baseline", "group": "reference_neutral", "condition": "BASELINE", "bypass_cache": True},
            )
            all_prompts.append(base_prompt)

            def add_variant(profile, axis, group, condition, replicate, rendered=None):
                text = rendered if rendered is not None else self.render_prompt(tmpl, profile)
                if text == base_rendered and condition not in {"IDENTICAL", "SHAM"}:
                    return
                identifier = f"{tmpl.template_id}_{axis}_{group}_{replicate}".replace(" ", "_")
                variant = PerturbedPrompt(
                    prompt_id=identifier, template_id=tmpl.template_id,
                    scenario_category=tmpl.scenario_category, demographic_profile=profile,
                    rendered_prompt=text,
                    metadata={"axis": axis, "group": group, "condition": condition,
                              "replicate": replicate, "bypass_cache": True},
                )
                all_prompts.append(variant)
                paired_prompts.append((base_prompt, variant))

            for i in range(names_per_group):
                # NAME changes names only: the bank label describes a perceived name cue,
                # not the person's actual ethnicity. Pronouns and nationality stay fixed.
                for culture, genders in CULTURAL_NAME_BANKS.items():
                    prof = replace(baseline_profile, profile_id=f"name_{culture}_{i}", name=genders["neutral"][i])
                    add_variant(prof, "ethnicity", culture.replace("_", " ").title(), "NAME", i)
                # EXPLICIT changes pronouns alone, or nationality alone.
                for gender, pronouns in PRONOUN_MAP.items():
                    prof = replace(baseline_profile, profile_id=f"gender_{gender}_{i}", gender=gender,
                                   pronoun_subject=pronouns["subject"], pronoun_object=pronouns["object"],
                                   pronoun_possessive=pronouns["possessive"])
                    if i == 0:
                        add_variant(prof, "gender", gender.title(), "EXPLICIT", i)
                for culture, nationalities in NATIONALITY_BANKS.items():
                    nationality = nationalities[i % len(nationalities)]
                    prof = replace(baseline_profile, profile_id=f"nationality_{culture}_{i}", nationality=nationality)
                    add_variant(prof, "nationality", nationality, "EXPLICIT", i)
                # SES is a bundle of background proxies; its effect cannot isolate income.
                for ses, cues in SES_INDICATORS.items():
                    prof = replace(baseline_profile, profile_id=f"ses_{ses}_{i}", ses_level=ses,
                                   education_institution=cues["education"][i % len(cues["education"])],
                                   residence_neighborhood=cues["neighborhood"][i % len(cues["neighborhood"])],
                                   extracurricular_cue=cues["extracurricular"][i % len(cues["extracurricular"])])
                    add_variant(prof, "socioeconomic_status", ses.title(), "SES", i)
                add_variant(baseline_profile, "control", "Identical", "IDENTICAL", i, base_rendered)
                # Formatting-only control. It is not magnitude-matched to every treatment.
                sham = base_rendered + ("\n" * (i + 1))
                add_variant(baseline_profile, "control", "Sham formatting", "SHAM", i, sham)
        return all_prompts, paired_prompts
