Faster R-CNN Implementation in Pytorch
========

This repository implements [Faster R-CNN](https://arxiv.org/abs/1506.01497) with training, inference and map evaluation in PyTorch.
The aim was to create a simple implementation based on PyTorch faster r-cnn codebase and to get rid of all the abstractions and make the implementation easy to understand.

The implementation caters to batch size of 1 only and uses roi pooling on single scale feature map.
The repo is meant to train faster r-cnn on voc dataset. Specifically I trained on VOC 2007 dataset.


## Data preparation
For setting up the VOC 2007 dataset:
* Download VOC 2007 train/val data from http://host.robots.ox.ac.uk/pascal/VOC/voc2007 and name it as `VOC2007` folder
* Download VOC 2007 test data from http://host.robots.ox.ac.uk/pascal/VOC/voc2007 and name it as `VOC2007-test` folder
* Place both the directories inside the root folder of repo according to below structure
    ```
    FasterRCNN-Pytorch
        -> VOC2007
            -> JPEGImages
            -> Annotations
        -> VOC2007-test
            -> JPEGImages
            -> Annotations
        -> tools
            -> train.py
            -> infer.py
            -> train_torchvision_frcnn.py
            -> infer_torchvision_frcnn.py
        -> config
            -> voc.yaml
        -> model
            -> faster_rcnn.py
        -> dataset
            -> voc.py
    ```

## For training on your own dataset

* Copy the VOC config(`config/voc.yaml`) and update the [dataset_params](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/config/voc.yaml#L1) and change the [task_name](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/config/voc.yaml#L35) as well as [ckpt_name](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/config/voc.yaml#L41) based on your own dataset.
* Copy the VOC dataset(`dataset/voc.py`) class and make following changes:
   * Update the classes list [here](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/dataset/voc.py#L61) (excluding background).
   * Modify the [load_images_and_anns](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/dataset/voc.py#L13) method to returns a list of im_infos for all images, where each im_info is a dictionary with following keys:
     ```        
      im_info : {
		'filename' : <image path>
		'detections' : 
			[
				'label': <integer class label for this detection>, # assuming the same order as classes list present above, with background as zero index.
				'bbox' : list of x1,y1,x2,y2 for the bboxes.
			]
	    }
     ```
* Ensure that `__getitem__` returns the following:
  ```
  im_tensor(C x H x W) , 
  target{
        'bboxes': Number of Gts x 4,
        'labels': Number of Gts,
        }
  file_path(just used for debugging)
  ```
* Change the training script to use your dataset [here](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/tools/train_torchvision_frcnn.py#L41)
* Then run training with the desired config passed as argument.


## Differences from Faster RCNN paper
This repo has some differences from actual Faster RCNN paper.
* Caters to single batch size
* Uses a randomly initialized fc6 fc7 layer of 1024 dim.
* Most of the hyper-parameters have directly been picked from official version and have not been tuned to this setting of 1024 dimensional fc layers. As of now using this I am getting ~61-62% mAP.
* To improve the results one can try the following:
  * Use VGG fc6 and fc7 layers
  * Tune the weight of different losses
  * Experiment with roi batch size
  * Experiment with hard negative mining

## For modifications 
* To change the fc dimension , change `fc_inner_dim` in config
* To use a different backbone, make the change [here](https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul/tree/main/FasterRCNN/model/faster_rcnn.py#L748) and also change `backbone_out_channels` in config
* To use hard negative mining change `roi_low_bg_iou` to say 0.1(this will ignore proposals with < 0.1 iou)
* To use gradient accumulation change `acc_steps` in config to > 1

# Quickstart
* Create a new conda environment with python 3.8 then run below commands
* ```git clone https://github.com/anjul1008/LearnComputerVisionFromScratchWithAnjul.git```
* ```cd FasterRCNN-PyTorch```
* ```pip install -r requirements.txt```
* For training/inference use the below commands passing the desired configuration file as the config argument . 
* ```python -m tools.train``` for training Faster R-CNN on voc dataset
* ```python -m tools.infer --evaluate False --infer_samples True``` for generating inference predictions
* ```python -m tools.infer --evaluate True --infer_samples False``` for evaluating on test dataset

## Using torchvision FasterRCNN 
* For training/inference using torchvision faster rcnn codebase, use the below commands passing the desired configuration file as the config argument.
* ```python -m tools.train_torchvision_frcnn``` for training using torchvision pretrained Faster R-CNN class on voc dataset
   * This uses the following arguments other than config file
   * --use_resnet50_fpn
      * True(default) - Use pretrained torchvision faster rcnn
      * False - Build your own custom model using torchvision faster rcnn class)
* ```python -m tools.infer_torchvision_frcnn``` for inference and testing purposes. Pass the desired configuration file as the config argument.
   * This uses the following arguments other than config file
   * --use_resnet50_fpn
      * True(default) - Use pretrained torchvision faster rcnn
      * False - Build your own custom model using torchvision faster rcnn class)
      * Should be same value as used during training
   * --evaluate (Whether to evaluate mAP on test dataset or not, default value is False)
   * -- infer_samples (Whether to generate predicitons on some sample test images, default value is True)

## Configuration
* ```config/voc.yaml``` - Allows you to play with different components of faster r-cnn on voc dataset  


## Output 
Outputs will be saved according to the configuration present in yaml files.

For every run a folder of ```task_name``` key in config will be created

During training of FasterRCNN the following output will be saved 
* Latest Model checkpoint in ```task_name``` directory

During inference the following output will be saved
* Sample prediction outputs for images in ```task_name/samples/*.png``` 
