#!/usr/bin python3
import numpy as np

__author__ = "Anjul Rajendra Sharma"


def get_iou(a, b):
    a_x1, a_y1, a_x2, a_y2 = a
    b_x1, b_y1, b_x2, b_y2 = b
    
    # assert a_x2 > a_x1, 'x cordinates are invalid'
    # assert b_x2 > b_x1, 'x cordinates are invalid'
    # assert a_y2 > a_y1, 'y cordinates are invalid'
    # assert b_y2 > b_y1, 'y cordinates are invalid'
    
    x_left = max(a_x1, b_x1)
    y_top = max(a_y1, b_y1)
    
    x_right = min(a_x2, b_x2)
    y_bottom = min(a_y2, b_y2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    area_intersection = (y_bottom - y_top) * (x_right - x_left)
    
    a_area = (a_x2- a_x1) * (a_y2 - a_y1)
    b_area = (b_x2- b_x1) * (b_y2 - b_y1)
    
    area_union = float(a_area + b_area - area_intersection + 1e-9)
    
    iou = area_intersection / area_union
    return iou

# this implimantation is class independent
# can be implimented for class agnostic
def apply_nms(preds, nms_threshold=0.5):
    # preds = [[x1, y1, x2, y2, score], ...]
    # sort by confidance socre
    preds = sorted(preds, key=lambda k: k[-1])
    
    # final pred list
    keep_pred = []
    while len(preds) > 0:
        keep_pred.append(preds[0])
        preds = [
            box for box in preds[1:]
            if get_iou(keep_pred[-1][:-1], box[:-1]) < nms_threshold
        ]
    return keep_pred
    
    
def mAP(det_boxes, gt_boxes, iou_threshold=0.5, method='interp'):
    r"""
    Method to calculate Mean Average Precision between two sets of boxes.
    Each will be a list of dictionary containing predictions/gt for
    ALL classes.

    :param det_boxes: List[Dict[List[float]]] prediction boxes for ALL images
                    det_boxes = [
                        {
                            'person' : [[x1, y1, x2, y2, score], ...],
                            'car' : [[x1, y1, x2, y2, score], ...]
                            'class_with_no_detections' : [],
                            ...,
                            'class_K':[[x1, y1, x2, y2, score], ...]
                        },
                        {det_boxes_img_2},
                         ...
                        {det_boxes_img_N},
                    ]
    :param gt_boxes: List[Dict[List[float]]] ground truth boxes for ALL images
                    gt_boxes = [
                        {
                            'person' : [[x1, y1, x2, y2], ...],
                            'car' : [[x1, y1, x2, y2], ...]
                            'class_with_no_ground_truth_objects' : [],
                            ...,
                            'class_K':[[x1, y1, x2, y2], ...]
                        },
                        {gt_boxes_img_2},
                         ...
                        {gt_boxes_img_N},
                    ]
    :param iou_threshold: (float) Threshold used for true positive. Default:0.5
    :param method: (str) One of area/interp. Default:interp
    :return: mean_ap, all_aps: Tuple(float, Dict[float])
                mean_ap is MAP at the provided threshold.
                all_aps is ap for all categories
    """
    gt_labels = {cls_key for im_gt in gt_boxes for cls_key in im_gt.keys()}
    all_aps = {}
    # average precisions for ALL classes
    aps = []
    for idx, label in enumerate(gt_labels):
        # Get detection predictions of this class
        cls_dets = [
            [im_idx, im_dets_label] for im_idx, im_dets in enumerate(det_boxes)
            if label in im_dets for im_dets_label in im_dets[label]
        ]
        
        # cls_dets = [
        #   (0, [x1_0, y1_0, x2_0, y2_0, score_0]),
        #   ...
        #   (0, [x1_M, y1_M, x2_M, y2_M, score_M]),
        #   (1, [x1_0, y1_0, x2_0, y2_0, score_0]),
        #   ...
        #   (1, [x1_N, y1_N, x2_N, y2_N, score_N]),
        #   ...
        # ]
        
        # Sort them by confidence score
        cls_dets = sorted(cls_dets, key=lambda k: -k[1][-1])
        
        # For tracking which gt boxes of this class have already been matched
        gt_matched = [[False for _ in im_gts[label]] for im_gts in gt_boxes]
        # Number of gt boxes for this class for recall calculation
        num_gts = sum([len(im_gts[label]) for im_gts in gt_boxes])
        tp = [0] * len(cls_dets)
        fp = [0] * len(cls_dets)
        
        # For each prediction
        for det_idx, (im_idx, det_pred) in enumerate(cls_dets):
            # Get gt boxes for this image and this label
            im_gts = gt_boxes[im_idx][label]
            max_iou_found = -1
            max_iou_gt_idx = -1
            
            # Get best matching gt box
            for gt_box_idx, gt_box in enumerate(im_gts):
                gt_box_iou = get_iou(det_pred[:-1], gt_box)
                if gt_box_iou > max_iou_found:
                    max_iou_found = gt_box_iou
                    max_iou_gt_idx = gt_box_idx
            # TP only if iou >= threshold and this gt has not yet been matched
            if max_iou_found < iou_threshold or gt_matched[im_idx][max_iou_gt_idx]:
                fp[det_idx] = 1
            else:
                tp[det_idx] = 1
                # If tp then we set this gt box as matched
                gt_matched[im_idx][max_iou_gt_idx] = True
        # Cumulative tp and fp
        tp = np.cumsum(tp)
        fp = np.cumsum(fp)
        
        eps = np.finfo(np.float32).eps
        recalls = tp / np.maximum(num_gts, eps)
        precisions = tp / np.maximum((tp + fp), eps)
        
        if method == 'area':
            recalls = np.concatenate(([0.0], recalls, [1.0]))
            precisions = np.concatenate(([0.0], precisions, [0.0]))
            
            # Replace precision values with recall r with maximum precision value
            # of any recall value >= r
            # This computes the precision envelope
            for i in range(precisions.size - 1, 0, -1):
                precisions[i - 1] = np.maximum(precisions[i - 1], precisions[i])
            # For computing area, get points where recall changes value
            i = np.where(recalls[1:] != recalls[:-1])[0]
            # Add the rectangular areas to get ap
            ap = np.sum((recalls[i + 1] - recalls[i]) * precisions[i + 1])
        elif method == 'interp':
            ap = 0.0
            for interp_pt in np.arange(0, 1 + 1E-3, 0.1):
                # Get precision values for recall values >= interp_pt
                prec_interp_pt = precisions[recalls >= interp_pt]
                
                # Get max of those precision values
                prec_interp_pt = prec_interp_pt.max() if prec_interp_pt.size > 0.0 else 0.0
                ap += prec_interp_pt
            ap = ap / 11.0
        else:
            raise ValueError('Method can only be area or interp')
        if num_gts > 0:
            aps.append(ap)
            all_aps[label] = ap
        else:
            all_aps[label] = np.nan
    # compute mAP at provided iou threshold
    mean_ap = sum(aps) / (len(aps) + 1E-6)
    return mean_ap, all_aps
