#
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
from PIL import Image

import os
import sys
from tqdm import tqdm
from typing import Optional

###################################################################################################
class resnet(nn.Module):
    def __init__(self, cfg: Optional[dict] = None) -> None:
        super(resnet, self).__init__()

        # model arthitecture
        self.backbone = torchvision.models.resnet34(pretrained=False)
        # print(self.backbone)

        dim = 1000
        self.head= nn.Sequential(
            nn.Linear(dim, dim),
            nn.ReLU(),
            nn.Linear(dim, 2)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.head(x)
        return x

###################################################################################################
class Evaluator(object):
    def __init__(
        self,
        model: torch.nn.Module,
        image_path_list,
        device_type: Optional[str] = "cpu",
        *args,
        **kwargs,
    ) -> None:
        super(Evaluator, self).__init__()

        #
        self.model = model
        self.image_path_list = image_path_list
        self.device_type = device_type

        #
        self.device = torch.device(self.device_type)
        self.model = self.model.to(self.device)
        # self.model_ema = self.model_ema.to(self.device)

    def eval_one_epoch(self, isEMA: Optional[bool] = False):

        #
        # model = self.model if isEMA else self.model_ema
        model = self.model
        print("********************* Evaluating *********************")
        model.eval()

        #
        dataset_mean, dataset_std = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
        input_resolution = 224
        eval_transform_set = transforms.Compose(
            [
                transforms.Resize((input_resolution, input_resolution)),
                transforms.ToTensor(),
                transforms.Normalize(mean=dataset_mean, std=dataset_std),
            ]
        )

        #
        predictions = []
        with torch.no_grad():
            with open("311581013.txt", "w") as fw:
                for image in self.image_path_list:
                    
                    #
                    image = image.strip("\n")
                    inputs = Image.open(image)
                    inputs = eval_transform_set(inputs)
                    inputs = torch.unsqueeze(inputs, 0)
                    inputs = inputs.to(self.device)
                    
                    #
                    logits = model(inputs)

                    #
                    predictions = logits.argmax(dim=-1).detach().tolist()[0]
                    fw.write(f"{1 if predictions == 0 else 0}")

        return None

    def run(self):
        """ """
        print("=" * 80)
        predictions = self.eval_one_epoch()
        print("=" * 80)

###################################################################################################
def load_checkpoint(model: torch.nn.Module, 
                    optimizer: torch.optim.Optimizer,
                    gradient_scaler: torch.cuda.amp.GradScaler,
                    save_dir: str,
                    device_type: str,
                    *args, **kwargs):
    
    #
    # checkpoint_path = f"{save_dir}/checkpoint.pt"
    checkpoint_path = f"checkpoint_best_0.6533.pt"
    print("=" * 80)
    print("Restore from previous checkpoint, and load it on device {}".format(device_type))
    if device_type == "cpu":
        checkpoint = torch.load(checkpoint_path, map_location=torch.device(f"cpu"))
    else:
        checkpoint = torch.load(checkpoint_path, map_location=torch.device(f"cuda"))

    #
    is_eval = False
    if "mode" in kwargs:
        print(f"Start loading checkpoint from {checkpoint_path} with mode Evaluate")
        is_eval = True

    # #
    # model.load_state_dict(checkpoint["model_state_dict"])
    model.load_state_dict(checkpoint)
    # # model_ema.load_state_dict(checkpoint["model_ema_state_dict"])
    if not is_eval:
        optimizer.load_state_dict(checkpoint["optim_state_dict"])
        gradient_scaler.load_state_dict(checkpoint["gradient_scaler_state_dict"])
    epoch = -1

    # # Return best metric of model and model_ema from checkpoint
    # metrics = get_previous_checkpoint_metrics(save_dir)
    # print(f"Restore model checkpoint with metric {metrics['best_model_metric']}")
    # # print(f"Restore model_ema checkpoint with metric {metrics['best_model_ema_metric']}")

    return model, optimizer, gradient_scaler, epoch + 1, None

###################################################################################################
#
def main_eval(image_path_list):
    
    #
    image_paths = []
    with open(image_path_list, "r") as fr:
        image_paths = fr.readlines()
    print(image_paths)

    #
    model = resnet() # getattr(models, model_type)()

    # Load from previous checkpint if there exists a useful checkpoint,
    #   or create a new checkpoint to store the training information
    device_type = "cpu"
    save_dir = ""
    # Resume the training that stop from previous training
    (
        model,
        _,
        _,
        _,
        _,
    ) = load_checkpoint(model, None, None, save_dir, device_type, mode="eval")

    ### Evaluator ###
    # Create a Evaluator instance and start training
    evaluator = Evaluator(
        model=model,
        image_path_list = image_paths,
        device_type=device_type
    )
    evaluator.run()

# Main entry point
if __name__ == "__main__":

    # Read arguments from input stream
    #   and then perform function via input command
    command = sys.argv[0]
    image_path_list = sys.argv[1]
    main_eval(image_path_list)
