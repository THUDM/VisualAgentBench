from utils import *
from agent import Agent
from env import Env

env, agent = None, None

def main(args):
    
    ret, msg = True, "None actions before"
    
    for _ in range(args.max_round):   
        obs = env.get_obs()
        log(args, f"[Round {_}] [Env] Current Reward {obs['reward']}\n", "yellow")
        if obs['done'] or obs['reward'] == 1.0:
            agent.server.step(None, None, obs['reward'], None, None, "task completed successfully")
            return True
        obs['return'] = ret
        obs['message'] = msg
        success, response, action = agent.step(obs)
        log(args, f"[Round {_}] [Agent] {response}\n", "cyan")
        if not success or action == "done()":
            return False
        ret, msg = env.step(action)
        log(args, f"[Round {_}] [Env] {msg}\n", "yellow")
    
    agent.server.step(None, None, obs['reward'], None, None, "task limit reached")
    return False


if __name__ == "__main__":

    args = parse_args_og()
    fix_seed(args.seed)
    env = Env(args)
    agent = Agent(args)

    if main(args):
        log(args, "Task completed successfully!\n", "green")
    else:
        log(args, "Task failed!\n", "red")

    env.close()
