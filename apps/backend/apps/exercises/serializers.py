"""The delivery contract follows Exercise and its authored child relationships."""
from urllib.parse import quote

from django.conf import settings
from rest_framework import serializers

from apps.exercises.models import (
    BlankAcceptedAnswer, Exercise, ExerciseAcceptedAnswer, ExerciseFillBlankSlot,
    ExerciseMatchingPair, ExerciseOption, ExerciseTarget, PromptBlock,
)
from apps.media.models import MediaAsset


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = ['id', 'media_type', 'storage_key', 'alt_text', 'url']

    def get_url(self, asset) -> str:
        return settings.CLOUDFRONT_DOMAIN.rstrip('/') + '/' + quote(asset.storage_key, safe='/')


class TargetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    sense_id = serializers.IntegerField()
    lexeme_id = serializers.CharField(source='sense.lexeme_id')
    label = serializers.CharField(source='sense.lexeme.lemma')
    meaning = serializers.CharField(source='sense.meaning')

    class Meta:
        model = ExerciseTarget
        fields = ['id', 'sense_id', 'lexeme_id', 'label', 'meaning']


class PromptBlockSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    text = serializers.SerializerMethodField()

    def get_text(self, block) -> str:
        return '' if block.block_type == 'media' else block.source_text
    media = MediaSerializer(read_only=True, allow_null=True)

    class Meta:
        model = PromptBlock
        fields = ['id', 'position', 'block_type', 'text', 'media']


class OptionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    media = MediaSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ExerciseOption
        fields = ['id', 'position', 'text', 'media', 'is_correct']


class AcceptedAnswerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = ExerciseAcceptedAnswer
        fields = ['id', 'text', 'is_primary']


class BlankAnswerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = BlankAcceptedAnswer
        fields = ['id', 'text']


class BlankSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    source_block_id = serializers.UUIDField()
    target_id = serializers.UUIDField(allow_null=True)
    accepted_answers = BlankAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = ExerciseFillBlankSlot
        fields = ['id', 'position', 'source_block_id', 'target_id', 'start_offset', 'end_offset', 'explanation', 'accepted_answers']


class MatchingPairSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    target_id = serializers.UUIDField(allow_null=True)
    left_media = MediaSerializer(read_only=True, allow_null=True)
    right_media = MediaSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ExerciseMatchingPair
        fields = ['id', 'position', 'target_id', 'left_text', 'left_media', 'right_text', 'right_media']


class ExerciseSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source='language.code')
    targets = TargetSerializer(many=True, read_only=True)
    prompt_blocks = PromptBlockSerializer(many=True, read_only=True)
    options = OptionSerializer(many=True, read_only=True)
    accepted_answers = AcceptedAnswerSerializer(many=True, read_only=True)
    fill_blank_slots = BlankSerializer(many=True, read_only=True)
    matching_pairs = MatchingPairSerializer(many=True, read_only=True)
    explanation_media = MediaSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Exercise
        fields = ['id', 'exercise_type', 'instruction', 'language', 'level', 'explanation', 'explanation_media',
                  'case_sensitive', 'ignore_punctuation', 'ignore_diacritics', 'targets', 'prompt_blocks',
                  'options', 'accepted_answers', 'fill_blank_slots', 'matching_pairs']


class LessonSessionStartSerializer(serializers.Serializer):
    pass  # Starts are always fresh; callers cannot retrieve an earlier delivery.


class LessonResponseSerializer(serializers.Serializer):
    exercise_id = serializers.UUIDField()
    response = serializers.JSONField()
    recall_ratings = serializers.JSONField(required=False, allow_null=True)


class LessonBatchSubmitSerializer(serializers.Serializer):
    responses = LessonResponseSerializer(many=True, allow_empty=False, max_length=100)


class SubmissionReceiptSerializer(serializers.Serializer):
    lesson_attempt_id = serializers.UUIDField()
    submitted = serializers.BooleanField()


class LessonMetadataSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)


class LessonSessionPayloadSerializer(SubmissionReceiptSerializer):
    learner_id = serializers.CharField()
    lesson = LessonMetadataSerializer()
    exercises = ExerciseSerializer(many=True)
