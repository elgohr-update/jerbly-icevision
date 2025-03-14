__all__ = ["BaseRecord", "autofix_records"]

from icevision.imports import *
from icevision.utils import *
from collections.abc import MutableMapping
from icevision.core import tasks
from icevision.core.exceptions import *
from icevision.core.components import *
from icevision.core.record_components import *


# TODO: MutableMapping because of backwards compatability
# TODO: Rename to Record
class BaseRecord(TaskComposite):
    base_components = {RecordIDRecordComponent, SizeRecordComponent}

    def as_dict(self) -> dict:
        return self.reduce_on_components("as_dict", reduction="update")

    def num_annotations(self) -> Dict[str, int]:
        return self.reduce_on_components("_num_annotations", reduction="update")

    def check_num_annotations(self):
        tasks_num_annotations = self.num_annotations()
        for task, num_annotations in tasks_num_annotations.items():
            if len(set(num_annotations.values())) > 1:
                msg = "\n".join(
                    [f"\t- {v} for {k}" for k, v in num_annotations.items()]
                )
                raise AutofixAbort(
                    "Number of items should be the same for each annotation type"
                    f", but got for task {task}:\n{msg}"
                )

    def autofix(self):
        self.check_num_annotations()

        tasks_success_dict = self.reduce_on_components("_autofix", reduction="update")

        for task_name, success_dict in tasks_success_dict.items():
            success_list = np.array(list(success_dict.values()))
            if len(success_list) == 0:
                continue
            keep_mask = reduce(np.logical_and, success_list)
            discard_idxs = np.where(keep_mask == False)[0]

            for i in discard_idxs:
                logger.log(
                    "AUTOFIX-REPORT",
                    "Removed annotation with index: {}, "
                    "for more info check the AUTOFIX-FAIL messages above",
                    i,
                )
                self.remove_annotation(task_name=task_name, i=i)

        return tasks_success_dict

    # TODO: Might have weird interaction with task_components
    def remove_annotation(self, i: int, task_name: str):
        self.reduce_on_task_components("_remove_annotation", task_name=task_name, i=i)

    def aggregate_objects(self):
        return self.reduce_on_components("_aggregate_objects", reduction="update")

    # Instead of copying here, copy outside?
    def load(self) -> "BaseRecord":
        record = deepcopy(self)
        record.reduce_on_components("_load")
        return record

    def unload(self):
        self.reduce_on_components("_unload")

    def setup_transform(self, tfm):
        self.reduce_on_components("setup_transform", tfm=tfm)

    def builder_template(self) -> List[str]:
        res = self.reduce_on_components("builder_template", reduction="extend").values()
        return [line for lines in res for line in lines]

    def __repr__(self) -> str:
        tasks_reprs = self.reduce_on_components("_repr", reduction="extend")

        def join_one(reprs):
            return "".join(f"\n\t- {o}" for o in reprs)

        reprs = [f"{task}: {join_one(reprs)}" for task, reprs in tasks_reprs.items()]
        repr = "\n".join(reprs)

        return f"{self.__class__.__name__}\n\n{repr}"

    # # backwards compatiblity: implemented method to behave like a dict
    # def __getitem__(self, key):
    #     return self.as_dict()[key]

    # def __setitem__(self, key, value):
    #     setattr(self, key, value)

    # def __delitem__(self, key):
    #     delattr(self, key)

    # def __iter__(self):
    #     yield from self.as_dict()

    # def __len__(self):
    #     return len(self.as_dict())


def autofix_records(records: Sequence[BaseRecord]) -> Sequence[BaseRecord]:
    keep_records = []
    for record in records:

        def _pre_replay():
            logger.log(
                "AUTOFIX-START",
                "️🔨  Autofixing record with record_id: {}  ️🔨",
                record.record_id,
            )

        with ReplaySink(_pre_replay) as sink:
            try:
                record.autofix()
                keep_records.append(record)
            except AutofixAbort as e:
                logger.warning(
                    "🚫 Record could not be autofixed and will be removed because: {}",
                    str(e),
                )

    return keep_records
