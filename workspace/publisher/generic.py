from gwaio.publisher.core import Collect, Push
from pathlib import Path


class CollectTask(Collect):
    name = "task"
    collect_type = None
    info = "Unique identifier for the task in the publishing context."

    def process(self, context):
        self.value = context.get_data("plugin").last_task_clicked


class CollectPreview(Collect):
    name = "preview"
    collect_type = str
    info = "Path to the preview image for the version."
    extension = ".jpg"

    def process(self, context):
        if not self.value:
            for file in context.get_data("plugin")._current_selected_files:
                if Path(file).suffix == self.extension:
                    self.value = str(file)
        if self.value:
            if (
                not Path(self.value).exists()
                or Path(self.value).suffix != self.extension
            ):
                raise Exception("Preview not valid.")
        else:
            raise Exception("Preview not valid.")


class CollectFile(Collect):
    name = "file"
    collect_type = str
    info = "Path to the file for the version."
    extension = ".ma"

    def process(self, context):
        if not self.value:
            for file in context.get_data("plugin")._current_selected_files:
                if Path(file).suffix == self.extension:
                    self.value = str(file)
        if self.value:
            if (
                not Path(self.value).exists()
                or Path(self.value).suffix != self.extension
            ):
                raise Exception("File not valid.")
        else:
            raise Exception("File not valid.")


class CollectFileScript(CollectFile):
    extension = ".pdf"


class CollectPreviewScript(CollectPreview):
    extension = ".pdf"


class CollectFileConcept(CollectFile):
    extension = ".psd"


class CollectFileAudio(CollectFile):
    extension = ".wav"


class CollectPreviewAudio(CollectPreview):
    extension = ".wav"


class CollectFileVideo(CollectFile):
    extension = ".mov"


class CollectPreviewVideo(CollectPreview):
    extension = ".mov"


class CollectEDL(CollectFile):
    extension = ".edl"


class CollectTimelog(Collect):
    name = "timelog"
    collect_type = int
    compulsory = True
    info = "Indicate the time (hours) it has taken to complete this version."

    def process(self, context):
        try:
            if self.value is None:
                raise
            self.value = int(self.value) * 60
        except:
            self.add_error(
                "Bad Timelog",
                "please use integers numbers.",
                [
                    [
                        "please use integers numbers.",
                        "",
                    ]
                ],
            )


class CollectDescription(Collect):
    name = "description"
    collect_type = str
    info = "Short description or summary of the task."

    def process(self, context):
        try:
            if self.value is None:
                raise
            str(self.value)
        except:
            raise Exception("Description not found.")


class PushSG(Push):
    name = "Push Version"

    def process(self, context):
        result = context.get_data("plugin").publish_version(
            context.get_data("task"),
            context.get_data("preview"),
            context.get_data("file"),
            context.get_data("description"),
        )
        if not result.get("success"):
            self.add_error(
                result.get("error"),
                result.get("message"),
                [[result.get("message"), ""]],
            )


class PushTimelog(Push):
    name = "Push Timelog"

    def process(self, context):
        result = context.get_data("plugin").publish_timelog(
            context.get_data("task"),
            context.get_data("timelog"),
        )
        if not result.get("success"):
            self.add_error(
                result.get("error"),
                result.get("message"),
                [[result.get("message"), ""]],
            )