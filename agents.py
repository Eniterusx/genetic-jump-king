import random


class Agent:
    def __init__(self, genome=None):
        self.genome = genome if genome else self.generate_genome()
        self.mutation_rate = 0.01
        self.recent_mutation_rate = 0.05
        self.recent_amount = 5
        self.fitness = 0
        self.current_step = 0

    def generate_genome(self):
        length = 150
        directions = [-1, 0, 1]
        jump_power = [0.65, 0.85, 1.05, 1.25, 1.45, 1.65, 1.85, 2.05, 2.25, 2.45]
        genome = []
        for _ in range(length):
            genome.append(
                (directions[random.randint(0, 2)], jump_power[random.randint(0, 9)])
            )
        return genome

    def get_step(self):
        if self.current_step >= len(self.genome):
            return None
        step = self.genome[self.current_step]
        self.current_step += 1
        return step


def selection(agents):
    best_num = 5
    agents.sort(key=lambda x: x.fitness, reverse=True)
    return agents[:best_num]


def crossover(agents):
    num_agents = 100
    new_agents = []
    for _ in range(num_agents):
        parent1 = random.choice(agents)
        parent2 = random.choice(agents)
        new_genome = []
        for i in range(len(parent1.genome)):
            if random.random() < 0.5:
                new_genome.append(parent1.genome[i])
            else:
                new_genome.append(parent2.genome[i])
        child = Agent(new_genome)
        new_agents.append(child)
    return new_agents


def mutation(agents, final_step):
    # 1% for a mutation to occur anywhere
    # 5% for a mutation to occur in the last 5 steps before the death of the agent

    # 50% for a gene to be replaced
    # 50% for a gene to be popped and appended to the end
    for agent in agents:
        indices = list(range(len(agent.genome)))
        for i in indices:
            if final_step - agent.recent_amount <= i <= final_step:
                if random.random() < agent.recent_mutation_rate:
                    if random.random() < 0.5:
                        # Replace the gene
                        agent.genome[i] = (
                            random.choice([-1, 0, 1]),
                            random.choice(
                                [
                                    0.65,
                                    0.85,
                                    1.05,
                                    1.25,
                                    1.45,
                                    1.65,
                                    1.85,
                                    2.05,
                                    2.25,
                                    2.45,
                                ]
                            ),
                        )
                    else:
                        # Pop the gene and append it to the end
                        gene = agent.genome.pop(i)
                        agent.genome.append(gene)
            elif random.random() < agent.mutation_rate:
                if random.random() < 0.5:
                    # Replace the gene
                    agent.genome[i] = (
                        random.choice([-1, 0, 1]),
                        random.choice(
                            [0.65, 0.85, 1.05, 1.25, 1.45, 1.65, 1.85, 2.05, 2.25, 2.45]
                        ),
                    )
                else:
                    # Pop the gene and append it to the end
                    gene = agent.genome.pop(i)
                    agent.genome.append(gene)
    return agents


def save_agents(agents, filename):
    with open(filename, "w") as f:
        for agent in agents:
            f.write(f"{agent.genome}\n")


def load_agents(filename):
    agents = []
    with open(filename, "r") as f:
        for line in f:
            genome = eval(line)
            agents.append(Agent(genome))
    return agents


def reproduce(agents, final_step, iteration):
    best_agents = selection(agents)
    new_agents = crossover(best_agents)
    new_agents = mutation(new_agents, final_step)
    save_agents(new_agents, f"agents/agents_{iteration}.txt")
    return new_agents


def populate(load_file=None):
    num_agents = 100
    agents = []
    if load_file:
        agents = load_agents(load_file)
        return agents
    for _ in range(num_agents):
        agents.append(Agent())
    return agents
