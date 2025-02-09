import pytest
from icevision.all import *


def _test_preds(preds):
    assert len(preds) == 1

    pred = preds[0].pred
    assert len(pred.detection.scores) == 2

    np.testing.assert_equal(pred.detection.label_ids, [2, 1])

    assert isinstance(pred.detection.bboxes[0], BBox)
    bboxes_np = np.array([bbox.xyxy for bbox in pred.detection.bboxes])
    bboxes_expected = np.array([[66, 57, 169, 257], [114, 222, 350, 285]])
    np.testing.assert_allclose(bboxes_np, bboxes_expected, atol=1)


def test_efficient_det_predict(fridge_efficientdet_model, fridge_efficientdet_records):
    fridge_efficientdet_model.eval()

    ds = fridge_efficientdet_records
    preds = efficientdet.predict(model=fridge_efficientdet_model, dataset=ds)

    _test_preds(preds)


def test_efficient_det_predict_dl(
    fridge_efficientdet_model, fridge_efficientdet_records
):
    fridge_efficientdet_model.eval()

    infer_dl = efficientdet.infer_dl(fridge_efficientdet_records, batch_size=1)
    preds = efficientdet.predict_dl(
        model=fridge_efficientdet_model, infer_dl=infer_dl, show_pbar=False
    )

    _test_preds(preds)


def test_efficient_det_predict_dl_threshold(
    fridge_efficientdet_model, fridge_efficientdet_records
):
    fridge_efficientdet_model.eval()

    infer_dl = efficientdet.infer_dl(fridge_efficientdet_records, batch_size=1)
    preds = efficientdet.predict_dl(
        model=fridge_efficientdet_model,
        infer_dl=infer_dl,
        show_pbar=False,
        detection_threshold=1.0,
    )

    assert len(preds[0].pred.detection.label_ids) == 0
