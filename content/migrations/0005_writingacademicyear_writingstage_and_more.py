# content/migrations/0005_writingacademicyear_writingstage_and_more.py

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_alter_unittestanswer_student_answer_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ── Step 1: Delete old writing models first ──────────
        # Must happen before creating new models to avoid
        # constraint conflicts during SQLite table remakes.

        migrations.DeleteModel(
            name='WritingPracticeAttempt',
        ),
        migrations.DeleteModel(
            name='WritingTestAttempt',
        ),
        migrations.DeleteModel(
            name='WritingPrompt',
        ),
        migrations.DeleteModel(
            name='ChunkWritingFocus',
        ),
        migrations.DeleteModel(
            name='UnitWritingTask',
        ),

        # ── Step 2: Create new system models ─────────────────

        migrations.CreateModel(
            name='WritingAcademicYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Example: 2025-2026', max_length=20)),
                ('start_date', models.DateField(help_text='Academic year start date. Class advancement happens automatically after this date.')),
                ('is_current', models.BooleanField(default=False, help_text='Mark exactly one academic year as current.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Academic Year',
                'verbose_name_plural': 'Academic Years',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='WritingStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(
                    help_text='Stage number 1–16.',
                    unique=True,
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(16),
                    ],
                )),
                ('name', models.CharField(max_length=100)),
                ('tier', models.CharField(
                    choices=[
                        ('sentence', 'Sentence'),
                        ('paragraph', 'Paragraph'),
                        ('genre', 'Genre'),
                    ],
                    max_length=20,
                )),
                ('eval_method', models.CharField(
                    choices=[
                        ('automatic', 'Automatic'),
                        ('keyword', 'Keyword'),
                        ('teacher', 'Teacher'),
                        ('ai_teacher', 'AI + Teacher'),
                    ],
                    help_text='How student work is evaluated at this stage.',
                    max_length=20,
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Plain English description shown to the student.',
                )),
                ('min_words_class_9',  models.PositiveSmallIntegerField(default=5)),
                ('min_words_class_10', models.PositiveSmallIntegerField(default=6)),
                ('min_words_class_11', models.PositiveSmallIntegerField(default=7)),
                ('min_words_class_12', models.PositiveSmallIntegerField(default=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Writing Stage',
                'verbose_name_plural': 'Writing Stages',
                'ordering': ['number'],
            },
        ),

        # ── Step 3: Create WritingStageContent ────────────────

        migrations.CreateModel(
            name='WritingStageContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_sentence_original', models.TextField(
                    help_text='Original sentence or passage taken directly from the unit text.',
                )),
                ('model_sentence_converted', models.TextField(
                    help_text='Simplified or converted version for comparison.',
                )),
                ('conversion_note', models.TextField(
                    help_text='Plain English explanation of what changed and why.',
                )),
                ('dissect_question', models.TextField(
                    help_text='The identification question shown to the student.',
                )),
                ('dissect_answer', models.TextField(
                    help_text='The correct answer used for automatic checking of Dissect phase.',
                )),
                ('imitate_frame', models.TextField(
                    help_text='The sentence or paragraph frame for the Imitate phase.',
                )),
                ('imitate_instruction', models.TextField(
                    default='Fill in the frame using your own words to make a correct sentence.',
                    help_text='Clear instruction for what the student should do with this frame.',
                )),
                ('produce_prompt', models.TextField(
                    help_text='The writing task for the Produce phase.',
                )),
                ('produce_instruction', models.TextField(
                    default='Write on your own. No frame is given. Use what you have learned in this unit.',
                    help_text='Clear instruction for the Produce phase.',
                )),
                ('required_keywords', models.TextField(
                    blank=True,
                    help_text='Comma-separated keywords the student must use.',
                )),
                ('min_word_count', models.PositiveSmallIntegerField(
                    blank=True,
                    help_text='Override the stage default minimum word count for this unit.',
                    null=True,
                )),
                ('ai_rubric', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Rubric for AI evaluation.',
                )),
                ('is_complete', models.BooleanField(
                    default=False,
                    help_text='Mark as complete when all content fields are filled and ready for students.',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('stage', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='stage_contents',
                    to='content.writingstage',
                )),
                ('unit', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='writing_stage_contents',
                    to='content.unit',
                )),
            ],
            options={
                'ordering': ['unit', 'stage__number'],
            },
        ),

        # ── Step 4: Create WritingAttempt ─────────────────────

        migrations.CreateModel(
            name='WritingAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phase', models.CharField(
                    choices=[
                        ('dissect', 'Dissect'),
                        ('imitate', 'Imitate'),
                        ('produce', 'Produce'),
                    ],
                    help_text='Which phase the student is submitting.',
                    max_length=10,
                )),
                ('attempt_number', models.PositiveSmallIntegerField(
                    help_text='Attempt number within this phase for this academic year.',
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('response_text', models.TextField(
                    help_text="The student's written response.",
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('passed', 'Passed'),
                        ('failed', 'Failed'),
                        ('cooldown', 'In Cooldown'),
                        ('approved', 'Approved by Teacher'),
                        ('needs_revision', 'Needs Revision'),
                    ],
                    default='pending',
                    help_text='Current status of this attempt.',
                    max_length=20,
                )),
                ('auto_checks', models.JSONField(blank=True, default=dict)),
                ('intervention_flags', models.JSONField(blank=True, default=list)),
                ('auto_score', models.PositiveSmallIntegerField(
                    blank=True, null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100),
                    ],
                )),
                ('ai_score', models.PositiveSmallIntegerField(
                    blank=True, null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100),
                    ],
                )),
                ('ai_feedback',      models.TextField(blank=True)),
                ('ai_rubric_scores', models.JSONField(blank=True, default=dict)),
                ('teacher_score', models.PositiveSmallIntegerField(
                    blank=True, null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100),
                    ],
                )),
                ('teacher_feedback',         models.TextField(blank=True)),
                ('reviewed_at',              models.DateTimeField(blank=True, null=True)),
                ('cooldown_task',            models.TextField(blank=True)),
                ('next_attempt_allowed_at',  models.DateTimeField(blank=True, null=True)),
                ('time_spent_seconds',       models.PositiveIntegerField(blank=True, null=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('academic_year', models.ForeignKey(
                    help_text='Academic year this attempt belongs to.',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='attempts',
                    to='content.writingacademicyear',
                )),
                ('content', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts',
                    to='content.writingstagecontent',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='writing_reviews',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='writing_attempts',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # ── Step 5: Create WritingIntervention ────────────────

        migrations.CreateModel(
            name='WritingIntervention',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sentence_text', models.TextField(
                    help_text='The exact sentence that triggered this intervention.',
                )),
                ('issue_label', models.CharField(
                    help_text='Plain English description of the problem.',
                    max_length=200,
                )),
                ('fix_exercise', models.TextField(
                    help_text='The single targeted exercise shown to the student.',
                )),
                ('student_fix',  models.TextField(blank=True)),
                ('is_resolved',  models.BooleanField(default=False)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
                ('resolved_at',  models.DateTimeField(blank=True, null=True)),
                ('attempt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='interventions',
                    to='content.writingattempt',
                )),
            ],
            options={
                'ordering': ['attempt', 'id'],
            },
        ),

        # ── Step 6: Create WritingStageMastery ────────────────

        migrations.CreateModel(
            name='WritingStageMastery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mastered_at', models.DateTimeField(
                    help_text='When mastery was first achieved.',
                )),
                ('mastered_via', models.CharField(
                    choices=[
                        ('automatic', 'Automatic'),
                        ('keyword', 'Keyword'),
                        ('teacher', 'Teacher'),
                        ('ai_teacher', 'AI + Teacher'),
                    ],
                    help_text='Which evaluation method granted mastery.',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('academic_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='masteries',
                    to='content.writingacademicyear',
                )),
                ('content', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='masteries',
                    to='content.writingstagecontent',
                )),
                ('mastery_attempt', models.ForeignKey(
                    blank=True, null=True,
                    help_text='The attempt that earned this mastery.',
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mastery_grants',
                    to='content.writingattempt',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='writing_masteries',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['mastered_at'],
            },
        ),

        # ── Step 7: Indexes and constraints ───────────────────

        migrations.AddIndex(
            model_name='writingintervention',
            index=models.Index(fields=['attempt'], name='content_wri_attempt_569bca_idx'),
        ),
        migrations.AddIndex(
            model_name='writingintervention',
            index=models.Index(fields=['is_resolved'], name='content_wri_is_reso_399c8c_idx'),
        ),
        migrations.AddIndex(
            model_name='writingstagecontent',
            index=models.Index(fields=['stage', 'unit'], name='content_wri_stage_i_c901d5_idx'),
        ),
        migrations.AddIndex(
            model_name='writingstagecontent',
            index=models.Index(fields=['is_complete'], name='content_wri_is_comp_3c204d_idx'),
        ),
        migrations.AddConstraint(
            model_name='writingstagecontent',
            constraint=models.UniqueConstraint(
                fields=('stage', 'unit'),
                name='unique_writing_content_per_stage_per_unit',
            ),
        ),
        migrations.AddIndex(
            model_name='writingattempt',
            index=models.Index(
                fields=['user', 'content', 'academic_year'],
                name='content_wri_user_id_0c940c_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='writingattempt',
            index=models.Index(fields=['user', 'phase'], name='content_wri_user_id_a9029c_idx'),
        ),
        migrations.AddIndex(
            model_name='writingattempt',
            index=models.Index(fields=['status'], name='content_wri_status_98e4f5_idx'),
        ),
        migrations.AddIndex(
            model_name='writingattempt',
            index=models.Index(fields=['reviewed_at'], name='content_wri_reviewe_0070bc_idx'),
        ),
        migrations.AddIndex(
            model_name='writingattempt',
            index=models.Index(
                fields=['next_attempt_allowed_at'],
                name='content_wri_next_at_117073_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='writingstagemastery',
            index=models.Index(
                fields=['user', 'academic_year'],
                name='content_wri_user_id_940ba3_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='writingstagemastery',
            index=models.Index(
                fields=['content', 'academic_year'],
                name='content_wri_content_18ee15_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='writingstagemastery',
            constraint=models.UniqueConstraint(
                fields=('user', 'content', 'academic_year'),
                name='unique_mastery_per_student_stage_year',
            ),
        ),
    ]