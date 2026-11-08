from collections import Counter

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.exercises.grading import normalize
from apps.exercises.models import Exercise



def validate_publishable(exercise):
    exercise.full_clean()
    targets = list(exercise.targets.select_related("sense__lexeme"))
    blocks = list(exercise.prompt_blocks.all())
    
    if not targets or not blocks:
        raise ValidationError("Provide a prompt and at least one learning target.")
    
    for obj in targets + blocks:
        obj.full_clean()
    
    policy = {name: getattr(exercise, name) for name in ("case_sensitive", "ignore_punctuation", "ignore_diacritics")}
    
    kind = exercise.exercise_type
    if kind == Exercise.Type.MULTIPLE_CHOICE:
        rows = list(exercise.options.all())
        
        if len(rows) < 2 or not any(row.is_correct for row in rows) or all(row.is_correct for row in rows):
            raise ValidationError("Choices need at least one correct option and one distractor.")
        
        labels = [(row.text.strip(), row.media_id) for row in rows]
        
        if len(labels) != len(set(labels)):
            raise ValidationError("Choice options must have distinguishable content.")
    
    elif kind in {Exercise.Type.FILL_BLANK, Exercise.Type.MATCHING}:
        rows = list(exercise.fill_blank_slots.all() if kind == Exercise.Type.FILL_BLANK else exercise.matching_pairs.all())
        
        if len(rows) < (2 if kind == Exercise.Type.MATCHING else 1):
            raise ValidationError("Provide blank slots or at least two matching pairs.")
        
        if kind == Exercise.Type.MATCHING:
            for side in ("left", "right"):
                labels = [(getattr(row, side + "_text").strip(), getattr(row, side + "_media_id")) for row in rows]
                if len(labels) != len(set(labels)):
                    raise ValidationError("Matching items on each side must be distinguishable.")
        
        for row in rows:
            if row.target_id is None and len(targets) != 1:
                raise ValidationError("Assign each blank or pair a target when testing multiple senses.")
            
            if kind == Exercise.Type.FILL_BLANK:
                answers = list(row.accepted_answers.all())
                
                if not answers:
                    raise ValidationError("Every blank needs at least one accepted answer.")
                
                for answer in answers:
                    answer.full_clean()
                    if not normalize(answer.text, policy):
                        raise ValidationError("A blank answer cannot normalize to empty text.")
        
        addressed = {row.target_id for row in rows if row.target_id}
        
        if len(targets) > 1 and addressed != {target.pk for target in targets}:
            raise ValidationError("Every learning target must be tested by a blank or pair.")
    else:
        rows = list(exercise.accepted_answers.all())
        
        if not rows:
            raise ValidationError("Provide at least one accepted answer.")
        
        if kind == Exercise.Type.WORD_ORDER:
            tiles = Counter(rows[0].text.split())
            
            if any(Counter(row.text.split()) != tiles for row in rows):
                raise ValidationError("All word-order answers must use the same word tiles.")
    
    for row in rows:
        row.full_clean()
        
        if hasattr(row, "text") and kind != Exercise.Type.MULTIPLE_CHOICE and not normalize(row.text, policy):
            raise ValidationError("An answer cannot normalize to empty text.")


@transaction.atomic
def publish_exercise(exercise_id):
    exercise = Exercise.objects.select_for_update().get(pk=exercise_id)
    
    if not exercise.is_published:
        validate_publishable(exercise)
        exercise.is_published = True
        exercise.published_at = timezone.now()
        
        models.Model.save(exercise, update_fields=["is_published", "published_at", "updated_at"])
    
    return exercise


@transaction.atomic
def unpublish_exercise(exercise_id):
    exercise = Exercise.objects.select_for_update().get(pk=exercise_id)
    
    if exercise.is_published:
        exercise.is_published = False
        exercise.published_at = None
        models.Model.save(exercise, update_fields=["is_published", "published_at", "updated_at"])
    
    return exercise


