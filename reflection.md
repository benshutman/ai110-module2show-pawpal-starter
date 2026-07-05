# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
##- 3 core actions a user should perform:   
    -Add/change pet/owner info (basic info re:owner and pet)
    -Add tasks (feeding, pet sitting, walks, playtime, grooming, medication)
    -Generate Daily Plan (Organizes tasks by time, priority, conflicts, etc)
- Briefly describe your initial UML design.
    -My UML describes 4 classes: Owner, Pet, Task, and Scheduler. For each class, the UML lists methods and attributes, and shows the relationship between the classes. 
- What classes did you include, and what responsibilities did you assign to each?
    - I included four classes: Owner, Pet, Task, and Scheduler. The Owner class manages the owner's information and the pets (multiple) that they might own. The Pet class stores each pet's information like name and species and age and the tasks connected to that pet. The Task class represents individual tasks, including duration, priority, and whether the task repeats. The Scheduler class sorts tasks and builds a plan based on the available time.

**b. Design changes**

- Did your design change during implementation?
    -My design was constantly changing during implementation. I kept interrogating the AI to help me design a better overall flow for the program logic. The base 4 classes are pretty "simple" but the process of designing a UML and asking for potential logical bottlenecks revealed some things. 
- If yes, describe at least one change and why you made it.
    -In my task class I didn't have a method to change the state and mark a task as completed, I was controlling it using a bool class attribute. I didn't have a way for Task to control it's own state. Claude suggested that I use a method to control Task state, which is better OOP design. Yeah, I forget my getters and setters! I happened to take a look at the gradiung rubric, which clearly says that we need a class method to control the state.  
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
