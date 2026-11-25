# **Tasty Bytes**
---
Project made by:
* Moșneag Sara 
* Rachieru Luiza Teodora
* Stoica Izabela
  
(325CC)
---
## **1. Introduction**
### **1.1. Overview**
The project aims to develop a web-based application designed to help users minimize food waste and simplify daily meal planning, using what they already have in the kitchen. The core concept revolves around a "fridge inventory" system: users input the ingredients they currently have available at home, and the application generates personalized recipe suggestions that use those specific items. Additionally, the application gives a detailed nutritional breakdown for each generated recipe.
### **1.2. Core Functionalities**
The application is structured around the following main features:
* **Ingredient Selection**: An interactive interface where users can easily check off the ingredients they currently have available
* **Recipe Matching**: An algorithm that processes the selected ingredients and returns the best matching recipes
* **Nutritional Statistics Calculator**: A feature that calculates an estimated breakdown of macronutrients (Calories, Protein, Carbohydrates, Fats) per serving based on the ingredient quantities
* **Recipe Management**: A user-friendly form allowing the addition of new recipes (including title, cooking time, servings, and instructions) directly into the database
* **Recipe Details**: A dedicated view showing information, instructions, and nutritional facts for any selected meal
### **1.3. Target Audience**
The application is primarily addressed to:
* **Students** who want to cook quick, budget-friendly meals with limited on-hand ingredients
* **Eco-conscious individuals** looking for practical tools to reduce household food waste
* **Health-conscious users** who require transparent nutritional tracking for their daily meals
### **1.4. Technologies & Implementation Constraints**
The system will be built as a client-server web application using a server-side rendering approach
* **Backend**: Developed in **Python**, utilizing the **FastAPI** framework to handle routing, business logic, and form submissions
* **Frontend**: Standard HTML, CSS, and basic JavaScript, rendered server-side using **Jinja2** templates to display data passed from the Python backend
* **Data Persistence**: A relational database (SQLite) will be used to store ingredients, recipes, and standard nutritional values

The entire codebase will be version-controlled using **Git**. The development team will utilize a collaborative Git workflow (with individual feature branches, rebasing, and merges) hosted on a remote repository platform (GitHub) to parallelize work and maintain code integrity.
---
## **2. System Overview**
### **2.1. Architecture**
* Client-server web application using server-side rendering.
* The browser sends HTTP requests to the FastAPI backend, which runs the business logic, queries the database and renders HTML pages with Jinja2 templates.
* Three layers:
  * **Presentation**: Jinja2 templates (HTML, CSS, basic JavaScript) for the ingredient checklist, recipe form, results list and recipe details.
  * **Application**: FastAPI routes, the recipe matching algorithm and the nutritional statistics calculator.
  * **Data**: SQLite database storing ingredients, recipes and nutritional values.
### **2.2. Communication Protocols**
* **GET** requests display pages (ingredient selection, recipe form, recipe details).
* **POST** requests submit forms (selected ingredient IDs, new recipe).
* After a recipe is added, the server redirects to the recipe list (Post/Redirect/Get), which prevents duplicate submissions on refresh.
* No separate JSON API: data goes directly from Python into the Jinja2 templates.
### **2.3. Database Structure**
* **ingredients**: id, name, calories, protein, carbs, fats (values per 100 g).
* **recipes**: id, title, cooking_time, servings, instructions.
* **recipe_ingredients**: recipe_id, ingredient_id, quantity (linking table for the many-to-many relationship between recipes and ingredients).

The same ingredients table is used for the checklist, the matching algorithm and the nutritional calculation, so recipes only contain known ingredients.
### **2.4. Technologies and Libraries**
* **Python** and **FastAPI** (routing, Form parameters, validation), run with Uvicorn.
* **Jinja2** for server-side HTML rendering, with HTML, CSS and basic JavaScript on the frontend.
* **SQLite** for persistence: no separate server needed, which is simple for a small team.
* **Git and GitHub** for collaborative version control.
### **2.5. Design Patterns and Paradigms**
* **Separation of concerns**: routes, business logic, database access and templates are kept apart.
* **MVC-like structure**: database = Model, Jinja2 templates = View, FastAPI routes = Controller.
* **Post/Redirect/Get** for form submissions.
* **Modular, function-based design**: small reusable functions (e.g. match percentage, nutritional values), which lets each team member work on a separate feature branch with fewer merge conflicts.
---
## **3. Detailed Component Design**
### **3.1. Adding a new recipe**
* **Functionality**: Provides a user-friendly method to add a new entry in the Data Base. It should include a title, the cooking time, a list of the ingredients, the number of servings and the instructions.
* **Implementation**:
  * **Frontend** (Jinja2 HTML Template): A simple HTML form rendered by Python, containing standard input fields and text areas.
  * **Backend** (FastAPI Route): A Python function handling the POST /recipes/new route. It uses FastAPI's Form parameters to capture the submitted data, validates it, and saves it directly to the database.
* **Interfaces & Communication**: The HTML form submits an HTTP POST request directly to the FastAPI backend, which then redirects the user to the recipe list upon success.
### **3.2. Ingredient selection**
* **Functionality**: An interactive page where users can check the boxes with the ingredients they have.
* **Implementation**:
  * **Frontend** (Jinja2 HTML Template): Python loops through the list of ingredients from the Data Base and generates an HTML form with checkboxes for every ingredient. 
  * **Backend** (FastAPI Route): A Python route that queries the database for all available ingredients and passes them as a Python list into the HTML template.
* **Interfaces & Communication**: The user checks the boxes and then clicks a button (“Search”), sending a list of selected ingredient IDs via an HTTPS POST request to Python.
### **3.3. Recipe matching**
* **Functionality**: The recommendation engine that compares the user’s selected ingredients with the ones from known recipes and then selects only those dishes that are a match.
* **Implementation**:
  * **Backend**: A Python program that calculates the match percentages and sorts the acceptable results (that are above a set standard).
* **Interfaces & Communication**: It is triggered by the FastAPI route handling ingredient selection from submission and it passes the sorted list of matching results to the result template.
### **3.4. Nutritional statistics**
* **Functionality**: It calculates some nutritional statistics based on the list of ingredients and their reported quantities. It should include Calories, Protein, Carbs and Fats per serving.
* **Implementation**:
  * **Backend**: A Python function that multiplies each ingredient’s quantity by its standard nutritional value. For this it is important to only have known ingredients in the recipes that are added to the Data Base.
* **Interfaces & Communication**: It is executed every time the details of a recipe are requested, passing the final computed numbers directly into the HTML template variables.
### **3.5. Recipe details**
* **Functionality**: Displays all the information related to a selected recipe in a readable format.
* **Implementation Details**:
  * **Frontend** (Jinja2 HTML Template): A template that uses Python template tags to display the data sent from the backend.
  * **Backend** (FastAPI Route): A Python route that queries the database for a specific recipe ID and renders the metadata into the template.
* **Interfaces & Communication**: Triggered when the user selects a recipe from the recommended results, sending an HTTP GET request to the FastAPI server.
---
## **4. Conclusion**
In the end, we hope to be able to build a working web-based application that handles a relational database. As we don't have much experience with Python, it surely will be a big challenge but we hope to be able to finish this project in less than 32h of work per person. We will have to learn how to work with FastAPI, Jinja2, SQLite and Python, and then put it into practice. This project will help us to get better at working in a team and to learn a few things about web-development. 
