from django.contrib import admin

from .models import Image
from .models import ImageAssignment


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = [
        "external_id",
        "ground_truth",
        "is_practice",
        "is_catch_trial",
        "source_dataset",
        "uploaded_at",
    ]
    list_filter = ["ground_truth", "is_practice", "is_catch_trial", "source_dataset"]
    search_fields = ["external_id", "source_dataset"]
    readonly_fields = ["uploaded_at"]


@admin.register(ImageAssignment)
class ImageAssignmentAdmin(admin.ModelAdmin):
    list_display = ["image", "participant", "condition"]
    list_filter = ["condition__study", "condition__name"]
    raw_id_fields = ["image", "participant"]
