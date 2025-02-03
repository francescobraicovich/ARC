import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
#from action_space import ARCActionSpace
from enviroment import maximum_overlap_regions, ARC_Env
import json
from sklearn.manifold import MDS
from dsl.utilities.padding import pad_grid, unpad_grid

def random_arc_problem(env):
    random_state = env.reset()
    grid, shape = random_state
    training_grid = grid[:, :, 0]
    unpadded_grid = unpad_grid(training_grid)
    return unpadded_grid

def random_array(env, arc_prob=1):
    """
    Generates a random 2D array for testing purposes.

    Returns:
        np.ndarray: A random 2D array.
    """
    if np.random.rand() < arc_prob:
        return random_arc_problem(env)
    
    rows = int(np.random.randint(3, 31))
    cols = int(np.random.randint(3, 31))
    return np.random.randint(0, 9, (rows, cols))

def create_color_similarity_matrix(action_space, env, num_experiments=10):
    color_selections = list(action_space.color_selection_dict.keys())
    n = len(color_selections)
    similarity_matrix = np.identity(n)

    for _ in range(num_experiments):
        random_problem = random_array(env, arc_prob=0.5)
        for i in range(n):
            for j in range(i + 1, n):
                selection1 = color_selections[i]
                selection2 = color_selections[j]
                col1 = action_space.color_selection_dict[selection1](random_problem)
                col2 = action_space.color_selection_dict[selection2](random_problem)
                
                similarity = 1 if col1 == col2 else 0
                similarity_matrix[i, j] += similarity
                similarity_matrix[j, i] += similarity
    mask = np.identity(n) == 0
    similarity_matrix[mask] /= num_experiments
    return similarity_matrix

def compute_selection_similarity(sel1, sel2):
    size = np.size(sel1)
    max = 0
    for i in range(sel1.shape[0]):
        for j in range(sel2.shape[0]):
            similarity = np.sum(sel1[i, :, :] == sel2[j, :, :]) / size
            if similarity > max:
                max = similarity
    return max

def create_selection_similarity_matrix(action_space, env, num_experiments=10):
    selections = list(action_space.selection_dict.keys())
    n = len(selections)
    similarity_matrix = np.identity(n)

    for _ in range(num_experiments):
        random_problem = random_array(env, arc_prob=0.85)
        random_color_in_problem = int(np.random.choice(np.unique(random_problem)))
        for i in range(n):
            for j in range(i + 1, n):
                selection1 = selections[i]
                selection2 = selections[j]
                sel1 = action_space.selection_dict[selection1](random_problem, color=random_color_in_problem)
                sel2 = action_space.selection_dict[selection2](random_problem, color=random_color_in_problem)
                similarity = compute_selection_similarity(sel1, sel2)
                similarity_matrix[i, j] += similarity
                similarity_matrix[j, i] += similarity
    mask = np.identity(n) == 0
    similarity_matrix[mask] /= num_experiments
    return similarity_matrix

def create_transformation_similarity_matrix(action_space, env, num_experiments=10):
    transformations = list(action_space.transformation_dict.keys())
    selections = list(action_space.selection_dict.keys())
    n = len(transformations)
    similarity_matrix = np.identity(n)

    for _ in range(num_experiments):
        random_problem = random_array(env, arc_prob=0.85)
        # Find a random selection that is not empty
        while True:
            random_color_in_problem = int(np.random.choice(np.unique(random_problem)))
            random_selection_key = np.random.choice(selections)
            random_selection = action_space.selection_dict[random_selection_key](random_problem, color=random_color_in_problem)
            random_action = np.array([1, random_selection_key, 0])
            if np.any(random_selection):
                break

        for i in range(n):
            for j in range(i + 1, n):
                transformation1 = transformations[i]
                transformation2 = transformations[j]

                random_action[2] = transformation1
                out1 = env.act(random_problem, random_action, fixed_color=random_color_in_problem)

                random_action[2] = transformation2
                out2 = env.act(random_problem, random_action, fixed_color=random_color_in_problem)
                r1, r2, similarity = maximum_overlap_regions(out1, out2)

                similarity_matrix[i, j] += similarity
                similarity_matrix[j, i] += similarity
    mask = np.identity(n) == 0
    similarity_matrix[mask] /= num_experiments
    return similarity_matrix

def filter_by_change(action_space, env, num_experiments, threshold):
    actions = action_space.get_space()
    n = len(actions)

    equal_ratios = np.zeros((n), dtype=np.float64)

    for i in range(n):
        action = actions[i]
        num_equal = 0
        
        for j in range(num_experiments):
            random_problem = random_arc_problem(env)
            new_state = env.act(random_problem, action)[0, :, :]
            if np.array_equal(random_problem, new_state):
                num_equal += 1

        equal_ratio = num_equal / num_experiments
        equal_ratios[i] = equal_ratio

        if i % 500 == 0:
            print(f'Filtered {i} out of {n} actions')

    print('Average equal ratio:', np.mean(equal_ratios))
    change_ratios = 1 - equal_ratios
    mask = change_ratios > threshold

    print(f'Out of {n} actions, only {np.sum(mask)} are used.')

    cleaned_actions = actions[mask]
    return cleaned_actions


def create_approximate_similarity_matrix(action_space, num_experiments_filter, filter_threshold, num_experiments_similarity):
    challenge_dictionary = json.load(open('data/RAW_DATA_DIR/arc-prize-2024/arc-agi_training_challenges.json'))
    env = ARC_Env(challenge_dictionary=challenge_dictionary, action_space=action_space)

    cleaned_actions = filter_by_change(action_space, env, num_experiments_filter, filter_threshold)

    color_similarity = create_color_similarity_matrix(action_space, env, num_experiments_similarity)
    print('Similarity matrix created for: color selections.')
    selection_similarity = create_selection_similarity_matrix(action_space, env, num_experiments_similarity)
    print('Similarity matrix created for: selections.')
    transformation_similarity = create_transformation_similarity_matrix(action_space, env, num_experiments_similarity)
    print('Similarity matrix created for: transformations.')

    color_selections = list(action_space.color_selection_dict.keys())
    selections = list(action_space.selection_dict.keys())
    transformations = list(action_space.transformation_dict.keys())

    n = len(cleaned_actions)
    similarity_matrix = np.identity(n, dtype=np.float32)

    for i in range(n):
        col_sel1 = color_selections.index(cleaned_actions[i][0])
        sel1 = selections.index(cleaned_actions[i][1])
        trn1 = transformations.index(cleaned_actions[i][2])
        for j in range(i+1, n):
            col_sel2 = color_selections.index(cleaned_actions[j][0])
            sel2 = selections.index(cleaned_actions[j][1])
            trn2 = transformations.index(cleaned_actions[j][2])
            similarity = color_similarity[col_sel1, col_sel2] * selection_similarity[sel1, sel2] * transformation_similarity[trn1, trn2]
            similarity_matrix[i, j] = similarity
            similarity_matrix[j, i] = similarity
        if i % 2500 == 0:
            print(f"Processed {i}/{n} actions.", end="\r")
    
    return cleaned_actions, similarity_matrix

def mds_embed(similarity_matrix, n_components=20):
    print('Embedding with MDS...')

    embedding = MDS(n_components=n_components, dissimilarity="precomputed", random_state=42, 
                    n_jobs=-1, metric=False, normalized_stress=True, n_init=1)
    
    embedding.fit(similarity_matrix)
    stress = embedding.stress_
    print(f'MDS stress: {stress}')
    return embedding.embedding_



"""
def create_similarity_matrix(action_space, env, num_experiments=10):
    actions = action_space.get_space()
    n = len(actions)
    similarity_matrix = np.identity(n)

    for _ in range(num_experiments):
        random_problem = random_array(env)
        transformation_time = 0
        similarity_time = 0
        for i in range(n):
            for j in range(i + 1, n):
                action1 = actions[i]
                action2 = actions[j]
                t0 = time()
                out1 = env.act(random_problem, action1)
                out2 = env.act(random_problem, action2)
                t1 = time()
                if np.shape(out1) != np.shape(out2):
                    r1, r2, similarity = maximum_overlap_regions(out1, out2)
                else:
                    similarity = np.sum(out1 == out2) / np.size(out2)
                #_, _, similarity2, _ = cross_correlate_best_overlap(out1, out2)
                #assert similarity == similarity2, f"Similarity mismatch: {similarity} != {similarity2}"

                similarity_matrix[i, j] += similarity
                similarity_matrix[j, i] += similarity
                t2 = time()
                transformation_time += t1 - t0
                similarity_time += t2 - t1

        similarity_matrix /= num_experiments
        return similarity_matrix
    
def compute_pair_similarity(i, j, actions, env, random_problem):

    action1 = actions[i]
    action2 = actions[j]
    out1 = env.act(random_problem, action1)
    out2 = env.act(random_problem, action2)
    r1, r2, similarity = maximum_overlap_regions(out1, out2)
    return (i, j, similarity)
    
def create_similarity_matrix_chunked(action_space, env, num_experiments=10, n_jobs=-1, chunk_size=500):
    actions = action_space.get_space()
    n = len(actions)
    similarity_matrix = np.identity(n, dtype=float)

    # Number of pairs can be insane, so chunk in blocks of 'block_size'
    block_size = 3  # tune to your memory & overhead constraints
    
    for exp_idx in range(num_experiments):
        random_problem = random_array(env)
        
        # We'll chunk over i in blocks of size block_size
        for start_i in tqdm(range(0, n, block_size), desc=f"Experiment {exp_idx+1}/{num_experiments}"):
            end_i = min(start_i + block_size, n)
            # Create sublist of pairs within this block
            pairs = [
                (i, j) 
                for i in range(start_i, end_i) 
                for j in range(i+1, n)
            ]
            # Parallel processing
            results = Parallel(n_jobs=n_jobs, batch_size=chunk_size)(
                delayed(compute_pair_similarity)(i, j, actions, env, random_problem) 
                for i, j in pairs
            )
            # Accumulate
            for i, j, sim in results:
                similarity_matrix[i, j] += sim
                similarity_matrix[j, i] += sim
        print(f"Processed experiment {exp_idx+1}/{num_experiments}")
    
    similarity_matrix /= num_experiments
    return similarity_matrix

"""