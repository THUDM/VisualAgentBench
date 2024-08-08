from jarvis.env.minecraft_env import Env
from jarvis.agent.minecraft_agent import Agent
from jarvis.utils import log, parse_args_minecraft, fix_seed

env, agent = None, None

def main(args, env, agent):

    obs = env.reset()
    reward = env.accumlated_reward
    done = env.done
    info = None

    for i in range(args.max_round):
        
        log(args, f"[Round {i}] [Env] Current Reward {reward}\n", "yellow")
        if done or reward == 1:
            agent.server.step(None, None, reward, None, "task completed successfully")
            return True
        
        success, response, action = agent.step(obs, info)

        log(args, f"[Round {i}] [Agent] {response}\n", "cyan")
        if not success:
            return False

        obs, reward, done, info = env.step(action)
        log(args, f"[Round {i}] [Env] {info['message']}\n", "yellow")
    
    agent.server.step(None, None, reward, None, "task limit reached")
    return False


if __name__ == '__main__':

    args = parse_args_minecraft()
    fix_seed(args.seed)
    # import os
    # os.environ["CUDA_VISIBLE_DEVICES"] = "2"
    log(args, args, "magenta")
    env = Env(args)
    agent = Agent(args)

    if main(args, env, agent):
        log(args, "Task completed successfully!\n", "green")
    else:
        log(args, "Task failed!\n", "red")

    env.close(write_video=args.write_video)
