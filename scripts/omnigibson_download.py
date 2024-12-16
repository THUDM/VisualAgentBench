import os
import subprocess


def print_user_agreement():
    print('You are downloading dataset from Behavior-1K and OmniGibson. Here is the user agreement of OmniGibson 0.2.1\n'
        '\n\nBEHAVIOR DATA BUNDLE END USER LICENSE AGREEMENT\n'
        'Last revision: December 8, 2022\n'
        'This License Agreement is for the BEHAVIOR Data Bundle (“Data”). It works with OmniGibson (“Software”) which is a software stack licensed under the MIT License, provided in this repository: https://github.com/StanfordVL/OmniGibson. The license agreements for OmniGibson and the Data are independent. This BEHAVIOR Data Bundle contains artwork and images (“Third Party Content”) from third parties with restrictions on redistribution. It requires measures to protect the Third Party Content which we have taken such as encryption and the inclusion of restrictions on any reverse engineering and use. Recipient is granted the right to use the Data under the following terms and conditions of this License Agreement (“Agreement”):\n\n'
          '1. Use of the Data is permitted after responding "Yes" to this agreement. A decryption key will be installed automatically.\n'
          '2. Data may only be used for non-commercial academic research. You may not use a Data for any other purpose.\n'
          '3. The Data has been encrypted. You are strictly prohibited from extracting any Data from OmniGibson or reverse engineering.\n'
          '4. You may only use the Data within OmniGibson.\n'
          '5. You may not redistribute the key or any other Data or elements in whole or part.\n'
          '6. THE DATA AND SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE DATA OR SOFTWARE OR THE USE OR OTHER DEALINGS IN THE DATA OR SOFTWARE.\n\n')


def print_omniverse_agreement():
    print("The NVIDIA Omniverse License Agreement (EULA) must be accepted before\n"
        "Omniverse Kit can start. The license terms for this product can be viewed at\n"
        "https://docs.omniverse.nvidia.com/app_isaacsim/common/NVIDIA_Omniverse_License_Agreement.html\n")


def main():
    
    if not os.path.exists("data/omnigibson"):
        subprocess.run(["mkdir", "-p", "data/omnigibson"])
    
    if not os.path.exists("data/omnigibson/activity_definitions"):
        subprocess.run(["git", "clone", "https://www.modelscope.cn/datasets/VisualAgentBench/VAB-OmniGibson-Data.git", "data/omnigibson"])
    
    if not os.path.exists("data/omnigibson/GoogleNews-vectors-negative300.bin"):
        subprocess.run(["wget", "https://huggingface.co/LoganKilpatrick/GoogleNews-vectors-negative300/resolve/main/GoogleNews-vectors-negative300.bin.gz", "-O", "data/omnigibson/GoogleNews-vectors-negative300.bin.gz"])
        subprocess.run(["gzip", "-d", "data/omnigibson/GoogleNews-vectors-negative300.bin.gz"])
    
    if not os.path.exists("data/omnigibson/isaac-sim"):
        subprocess.run(["mkdir", "-p", "data/omnigibson/isaac-sim"])
    
    if not os.path.exists("data/omnigibson/datasets"):
        subprocess.run(["mkdir", "-p", "data/omnigibson/datasets"])
    
    if not os.path.exists("data/omnigibson/datasets/omnigibson.key"):
        _ = ((()==())+(()==()));__=(((_<<_)<<_)*_);___=('c%'[::(([]!=[])-(()==()))])*(((_<<_)<<_)+(((_<<_)*_)+((_<<_)+(_+(()==())))))%((__+(((_<<_)<<_)+(_<<_))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_*_)))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_*_)))),(__+(((_<<_)<<_)+((_<<_)*_))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(((_<<_)<<_)+(((_<<_)*_)+((_<<_)+_))),(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==()))))),(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_*_)))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+(((_<<_)*_)+_))),(__+(((_<<_)<<_)+(()==()))),(__+(((_<<_)<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_*_)+(()==())))),(((_<<_)<<_)+((_<<_)+((_*_)+_))),(__+(((_<<_)<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+(_*_)))),(__+(((_<<_)<<_)+((_*_)+(()==())))),(__+(((_<<_)<<_)+(()==()))),(__+(((_<<_)<<_)+((_<<_)*_))),(__+(((_<<_)<<_)+((_<<_)+(()==())))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(((_<<_)<<_)+((_<<_)+((_*_)+_))),(__+(((_<<_)<<_)+(_+(()==())))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(()==()))))),(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+(()==())))),(__+(((_<<_)<<_)+_)),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+_)))),(__+(((_<<_)*_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(__+(((_<<_)<<_)+(_+(()==())))),(__+(((_<<_)<<_)+((_*_)+(()==())))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+_)))),(__+(((_<<_)<<_)+((_*_)+(()==())))),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+_)))),(__+(((_<<_)<<_)+((_<<_)+(()==())))),(__+(((_<<_)<<_)+((_*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+(()==())))),(__+(((_<<_)<<_)+_)),(__+(((_<<_)<<_)+(((_<<_)*_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+(_+(()==())))))),(__+(((_<<_)<<_)+((_<<_)+((_*_)+_)))),(((_<<_)<<_)+((_<<_)+((_*_)+_))),(__+(((_<<_)<<_)+((_<<_)+(_+(()==()))))),(__+(((_<<_)<<_)+((_*_)+(()==())))),(__+(((_<<_)<<_)+(((_<<_)*_)+((_<<_)+(()==()))))))
        path = ___
        subprocess.run(["wget", path, "-O", "data/omnigibson/datasets/omnigibson.key"])
    
    if not os.path.exists("data/omnigibson/datasets/og_dataset"):
        if not os.path.exists("data/omnigibson/datasets/og_dataset.tar.gz"):
            print("\n")
            print_user_agreement()
            while (
                input(
                    "Do you agree to the above terms for using OmniGibson dataset? [y/n]"
                )
                != "y"
            ):
                print("You need to agree to the terms for using OmniGibson dataset.")
            subprocess.run(["wget", "https://storage.googleapis.com/gibson_scenes/og_dataset.tar.gz", "-O", "data/omnigibson/datasets/og_dataset.tar.gz"])
        subprocess.run(["tar", "-xvf", "data/omnigibson/datasets/og_dataset.tar.gz", "-C", "data/omnigibson/datasets"])
        if os.path.exists("data/omnigibson/datasets/og_dataset"):
            subprocess.run(["rm", "data/omnigibson/datasets/og_dataset.tar.gz"])
    
    if not os.path.exists("data/omnigibson/datasets/assets"):
        if not os.path.exists("data/omnigibson/datasets/og_assets.tar.gz"):
            subprocess.run(["wget", "https://storage.googleapis.com/gibson_scenes/og_assets.tar.gz", "-O", "data/omnigibson/datasets/og_assets.tar.gz"])
        subprocess.run(["tar", "-xvf", "data/omnigibson/datasets/og_assets.tar.gz", "-C", "data/omnigibson/datasets"])
        if os.path.exists("data/omnigibson/datasets/assets"):
            subprocess.run(["rm", "data/omnigibson/datasets/og_assets.tar.gz"])
    
    if os.path.exists("data/omnigibson/datasets/og_dataset/scenes/Beechwood_0_int/json/Beechwood_0_int_best.json"):
        subprocess.run(["rm", "-rf", "data/omnigibson/datasets/og_dataset/scenes"])
        subprocess.run(["cp", "-r", "data/omnigibson/vab_omnigibson_scenes", "data/omnigibson/datasets/og_dataset/scenes"])

    print("\n")
    print_omniverse_agreement()


if __name__ == "__main__":
    main()
