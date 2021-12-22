import chronological
import openai
import os
import time
import aiofiles as aiof
# Stop Debug Logger Spam
chronological.logger.remove(None)
output = "outputs/story_output" + str(time.time()) + ".txt"

# var to save the current tldr, called in generateStory
current_tldr = ""

def third_person():
    pass


async def generate(prompt, max_tokens=100, temperature=0.5, top_p=1, frequency_penalty=0.5, stop=["\n\n"]):
    result = await chronological.cleaned_completion(prompt,
                                                    max_tokens=max_tokens,
                                                    engine="davinci",
                                                    temperature=temperature,
                                                    top_p=top_p,
                                                    frequency_penalty=frequency_penalty,
                                                    stop=stop)
    return result


async def init_story():

    # Default prompt
    prompt_id = 'example_prompt'

    # User input to choose prompt

    # you call the Chronology functions, awaiting the ones that are marked await
    # read_prompt() looks in prompts/ directory for a text file. Pass in file name only, not extension.
    # Example: prompts/hello-world.txt -> read_prompt('hello-world')
    prompt = chronological.read_prompt(prompt_id)
    result = await generate(prompt)

    story = prompt + ' ' + result

    # Return Initial Story
    return story


# generate summary state of most recently generated story
# take from tldr? maybe add more methods later. Maybe add the table method.
# when updating summary state to get new tldr feed it new input story and old tldr story
# use update_tldr for initial generation as well as updating
# some way of s
# newStory --> str
# firstStory --> bool
# tldrSummary --> str
# added updating current_tldr variable
async def update_tldr(newStory, firstStory=True, tldrSummary=""):

    if firstStory:
        tldrUpdated = openai.Completion.create(
            engine="davinci",
            prompt=newStory + "\n\n" + "tl;dr:",
            temperature=0.3,
            max_tokens=200,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        firstStory = False
        current_tldr = tldrUpdated

    else:

        tldrUpdated = openai.Completion.create(
            engine="davinci",
            prompt=tldrSummary + "\n\n" + newStory + "\n\n" + "tl;dr:",
            temperature=0.3,
            max_tokens=200,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        current_tldr = tldrUpdated

    return tldrUpdated


# separate out the story generation into separate function,     done
# have it take tldr as input,                                   done
# update tldr with function,                                    done   
# and output new tldr iteratively                               done

def generateStory():
    
    # update tldr with update_tldr
    update_tldr(init_story, firstStory=False, tldrSummary=current_tldr)
    
    return current_tldr


async def options_generator(prompt):
    results = []
    # Generate 4 story options
    for i in range(4):
        results.append(generate(prompt, max_tokens=50, temperature=0.5,
                       frequency_penalty=0.5, stop=["\n\n\n\n\n"]))
    choices = await chronological.gather(*results)
    return choices


async def choose_story(input_story):
    # display newStory
    print("\n\n" + input_story + "\n\n")

    choices = await options_generator(input_story)
    # print(choices)

    # Present Choices for Next Chapter
    x = 1
    for choice in choices:
        print(str(x) + ". " + choice + "\n")
        x += 1

    # User chooses option
    # selected_choice = whatever they end up picking
    try:
        user_input = int(input("Enter your choice number: "))
        # - 1 because choosing 1 is really choosing 0
        num = user_input - 1
        if num < 0 or num > x:
            raise ValueError
        else:
            selected_choice = choices[num]
            # write choice
            async with aiof.open(output, mode='a') as f:
                await f.write("input: " + selected_choice)
                await f.write('\n\n\n')
                await f.close()
    except ValueError:
        print("Please only input numbers for your choice, between 1 and 4")
    # Generate Chapter
    result = await generate(input_story + selected_choice, max_tokens=200, temperature=0.7, frequency_penalty=0.5)

    # Return Chapter
    return result


# you can name this function anything you want, the name "logic" is arbitrary
async def game():
    # Initial Story Choice
        story = await init_story()
        async with aiof.open(output, mode='a') as f:
            await f.write(story)
            await f.write('\n\n\n')
            await f.close()
        
        while True:
            story = await choose_story(story)
            # write story to file
            async with aiof.open(output, mode='a') as f:
                await f.write(story)
                await f.write('\n\n\n')
                await f.close()

# invoke the Chronology main fn to run the async logic
chronological.main(game)