from flask import Flask, jsonify, render_template, request, make_response
from flask_cors import CORS
from flask_restful import Resource, Api
from expenses_tracker.const import DATABASE_PATH, EXPENSES_TABLE_NAME, CATEGORIES_TABLE_NAME
from expenses_tracker.expense.Category import Category
from expenses_tracker.expense.Expense import Expense
from expenses_tracker.storage.ExpensesPersisterFactory import ExpensesPersisterFactory
from expenses_tracker.storage.ExpensesRetrieverFactory import ExpensesRetrieverFactory

app = Flask(__name__)
CORS(app)
api = Api(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.errorhandler(404)
def page_not_found(e):
    """Renders default 404 Page Not Found template"""
    return render_template("404.html"), 404

def get_expenses_retriever():
    retriever_factory = ExpensesRetrieverFactory()
    return retriever_factory.create("sqlite", DATABASE_PATH,
                                    EXPENSES_TABLE_NAME,
                                    CATEGORIES_TABLE_NAME)

def get_expenses_persister():
    persister_factory = ExpensesPersisterFactory()
    return persister_factory.create("sqlite", DATABASE_PATH,
                                    EXPENSES_TABLE_NAME,
                                    CATEGORIES_TABLE_NAME)

def convert_models_to_json(models):
    return list(map(lambda model: model.to_json(), models))

class Expenses(Resource):
    def get(self, category_id, month):
        expenses_retriever = get_expenses_retriever()
        expenses = expenses_retriever.retrieve_expenses(category_id, month)
        expenses_as_json = convert_models_to_json(expenses)

        return expenses_as_json

    def __convert_expenses_to_json(self, expenses):
        return map(lambda expense: expense.to_json(), expenses)

@app.route("/expense", methods = ["GET"])
def add_expense():
    if request.method == "GET":
        json_data = request.get_json(force=True)
        expense = Expense.from_json(json_data)
        persister = get_expenses_persister()

        persister.add_expense(expense)

        return jsonify(expense.to_json())

@app.route("/expense/<expense_id>", methods = ["GET", "PATCH", "DELETE"])
def update_expense(expense_id):
    if request.method == "PATCH":
        json_data = request.get_json(force=True)
        persister = get_expenses_persister()
        expense = persister.update_expense(expense_id, json_data)

        return jsonify(expense.to_json())

class ExpenseNames(Resource):
    def get(self, name):
        if not name:
            return jsonify([])

        expenses_retriever = get_expenses_retriever()
        expense_names = expenses_retriever.retrieve_similar_expense_names(name)

        return jsonify(expense_names)

class Categories(Resource):
    def get(self):
        expenses_retriever = get_expenses_retriever()
        categories = expenses_retriever.retrieve_categories()
        categories_as_json = convert_models_to_json(categories)

        return jsonify(categories_as_json)

    def post(self):
        json_data = request.get_json(force=True)
        category = Category.from_json(json_data)
        persister = get_expenses_persister()

        persister.add_category(category)

        expenses_retriever = get_expenses_retriever()
        categories = expenses_retriever.retrieve_categories()
        categories_as_json = convert_models_to_json(categories)

        return jsonify(categories_as_json)

class Statistics(Resource):
    def get(self, number_of_months):
        expenses_retriever = get_expenses_retriever()
        statistics = expenses_retriever.retrieve_statistics_for_months(int(number_of_months))
        statistics_as_json = convert_models_to_json(statistics)

        return jsonify(statistics_as_json)

class StatisticsMonthly(Resource):
    def get(self, number_of_months):
        expenses_retriever = get_expenses_retriever()
        statistics = expenses_retriever.retrieve_statistics_for_months(number_of_months)
        statistics_as_json = convert_models_to_json(statistics)

        return jsonify(statistics_as_json)

api.add_resource(Expenses, "/expenses/<category_id>/<month>")
api.add_resource(ExpenseNames, "/expense-names/<name>")
api.add_resource(Categories, "/categories")
api.add_resource(Statistics, "/statistics/<number_of_months>")

if __name__ == "__main__":
    app.run(debug=True)
