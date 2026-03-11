import factory
from factory.django import DjangoModelFactory

from mwhitestudy1.images.models import Image
from mwhitestudy1.images.models import ImageAssignment
from mwhitestudy1.participants.tests.factories import ParticipantSessionFactory
from mwhitestudy1.study.tests.factories import ConditionFactory


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = Image

    external_id = factory.Sequence(lambda n: f"image_{n:04d}")
    ground_truth = factory.Iterator([Image.MALIGNANT, Image.BENIGN])
    image_file = factory.django.ImageField(filename="test_image.png", width=100, height=100)
    is_practice = False
    is_catch_trial = False
    source_dataset = "test_dataset"

    class Params:
        practice = factory.Trait(is_practice=True)
        catch_trial = factory.Trait(is_catch_trial=True)


class ImageAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = ImageAssignment

    image = factory.SubFactory(ImageFactory)
    participant = factory.SubFactory(ParticipantSessionFactory)
    condition = factory.SubFactory(ConditionFactory)
