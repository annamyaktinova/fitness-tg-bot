from aiogram import Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from utils import get_temperature, get_food_info

router = Router()

class Form(StatesGroup):
    weight = State()
    height = State()
    age = State()
    gender = State()
    activity = State()
    city = State()
    calories = State()

class FoodState(StatesGroup):
    amount = State()

def calculate_calorie_goal(weight: int, height: int, age: int, gender: str, activity: int):
    if gender == 'М':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    if activity < 30:
        activity_factor = 1.2
    elif activity < 60:
        activity_factor = 1.375
    elif activity < 90:
        activity_factor = 1.55
    elif activity < 120:
        activity_factor = 1.725
    else:
        activity_factor = 1.9
    
    calorie_goal = bmr * activity_factor
    return calorie_goal

def calculate_water_goal(weight: int, activity: int, temperature: float):
    water_goal = 30 * weight + 500 * (activity / 30) + 500 * (temperature > 25)
    return int(water_goal)

def calculate_workout_calories(workout_type: str, duration: int, weight: int):
    # MET (метаболический эквивалент) для разных типов тренировок
    met_values = {
        'бег': 8.0,
        'ходьба': 3.5,
        'велосипед': 6.0,
        'плавание': 6.0,
        'йога': 3.0,
        'силовая': 5.0,
        'кардио': 7.0,
        'танцы': 5.0,
        'футбол': 7.0,
        'баскетбол': 6.5
    }
    
    met = met_values.get(workout_type.lower(), 5.0)  # по умолчанию 5.0
    calories = met * weight * (duration / 60)
    return round(calories, 1)

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    await message.reply("Добро пожаловать! Я ваш трекер питания и тренировок. \nВведите /help для получения списка доступных команд.")
    await state.clear() #сброс сценария в случае, если пользователь в процессе заполнения данных решает перезапустить бота

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/set_profile - настроить профиль\n\n"
        "Команды, доступные после заполнения профиля:\n"
        "/log_water <количество в мл> - записать количество выпитой воды в мл\n"
        "/log_food <название продукта> - записать еду\n"
        "/log_workout <вид тренировки> <время в мин> - записать тренировку\n"
        "/check_progress - посмотреть прогресс"
    )

@router.message(Command('set_profile'))
async def start_form(message: Message, state: FSMContext):
    await state.clear() #сброс сценария в случае, если пользователь в процессе заполнения данных решает заново заполнить профиль
    await message.answer("Введите Ваш вес (в кг)")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight=int(message.text)
    except ValueError:
        await message.answer("Введите вес в корректном формате (только число)")
        return
    
    if weight <= 0:
        await message.answer("Вес должен быть больше 0")
        return

    await state.update_data(weight=weight)

    await message.answer("Введите Ваш рост (в см)")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height=int(message.text)
    except ValueError:
        await message.answer("Введите рост в корректном формате (только число)")
        return
    
    if height <= 0:
        await message.answer("Рост должен быть больше 0")
        return

    await state.update_data(height=height)
    
    await message.answer("Введите Ваш возраст")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.answer("Введите возраст в корректном формате (только число)")
        return
    
    if (age > 120) or (age < 1):
        await message.answer("Введите корректный возраст (от 1 до 120)")
        return
    
    await state.update_data(age=age)

    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="М", callback_data='М')],
        [InlineKeyboardButton(text="Ж", callback_data='Ж')],
    ],
    input_field_placeholder="Ваш пол"
)
    await message.answer("Введите Ваш пол", reply_markup=keyboard)
    await state.set_state(Form.gender)

@router.callback_query(Form.gender)
async def process_sex(callback: CallbackQuery, state: FSMContext):
    gender = callback.data
    await state.update_data(gender=gender)
    await callback.message.answer("Сколько минут активности у Вас в день?")
    await state.set_state(Form.activity)

@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
    except ValueError:
        await message.answer("Введите уровень активности в корректном формате (только число)")
        return

    if (activity > 1440) or (activity <= 0):
        await message.answer("Пожалуйста, введите корректный уровень активности в минутах")
        return
    
    await state.update_data(activity=activity)
    await message.answer("В каком городе Вы находитесь?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()

    weight = data.get('weight')
    height = data.get('height')
    age = data.get('age')
    gender = data.get('gender')
    activity = data.get('activity')
    city = data.get('city')

    temperature = await get_temperature(city)
    calorie_goal = calculate_calorie_goal(weight, height, age, gender, activity)
    water_goal = calculate_water_goal(weight, activity, temperature)

    await state.update_data(water_goal=water_goal, calorie_goal=calorie_goal)
    await message.answer(
        f"Рассчитанная норма калорий: {calorie_goal:.0f} ккал/день\n"
        f"Норма воды: {water_goal:.0f} мл/день\n\n"
        "Если хотите установить другую цель по калориям, введите количество ккал (в противном случае введите 'нет')"
    )
    await state.set_state(Form.calories)

@router.message(Form.calories)
async def set_custom_goal(message: Message, state: FSMContext, db: Database):
    text = message.text.lower()
    if text != 'нет':
        if text.isdigit():
            await state.update_data(calorie_goal=int(message.text))
        else:
            await message.answer("Пожалуйста, введите корректное количество ккал или 'нет'")
            return

    data = await state.get_data()
    await db.save_user(message.from_user.id, data)

    await message.answer(
        "✅ Профиль сохранен!\n\n"
        "Ваши данные:\n"
        f"Вес: {data['weight']} кг\n"
        f"Рост: {data['height']} см\n"
        f"Возраст: {data['age']} лет\n"
        f"Пол: {data['gender']}\n"
        f"Активность: {data['activity']} мин/день\n"
        f"Город: {data['city']}\n\n"
        f"🎯 Цель по калориям: {data['calorie_goal']:.0f} ккал/день\n"
        f"💧 Цель по воде: {data['water_goal']:.0f} мл/день\n\n"
        "Теперь вы можете использовать команды:\n"
        "/log_water - записать количество выпитой воды в мл\n"
        "/log_food - записать еду\n"
        "/log_workout - записать тренировку\n"
        "/check_progress - посмотреть прогресс"
    )
    
    await state.clear()

@router.message(Command('log_water'))
async def cmd_log_water(message: Message, command: CommandObject, db: Database):
    #Проверка наличия профиля
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("Сначала настройте профиль: /set_profile")
        return

    #Проверка введенного количества воды
    command_args = command.args
    try:
        command_args = int(command_args)
    except:
        await message.answer("Пожалуйста, введите количество выпитой воды в мл в формате /log_water <количество>")
        return

    logged_water = command_args + user_data['logged_water'] #Суммируем количество всей выпитой воды

    remaining_water = user_data['water_goal'] - logged_water #Рассчитываем, сколько осталось выпить воды до достижения цели

    await db.log_water(logged_water)

    if remaining_water > 0:
        msg = f"Осталось: {remaining_water} мл"
    elif remaining_water < 0:
        msg = f"Цель перевыполнена на {-remaining_water} мл"
    else:
        msg = f"✅ Цель выполнена!"

    await message.answer(
        f"Записано: {command_args} мл\n"
        f"Всего выпито воды: {logged_water} мл\n" +
        msg
    )

@router.message(Command('log_food'))
async def cmd_log_food(message: Message, command: CommandObject, state: FSMContext, db: Database):
    #Проверка наличия профиля
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("Сначала настройте профиль: /set_profile")
        return

    #Проверка введенных аргументов
    command_args = command.args
    if command_args is None:
        await message.answer(
            "Пожалуйста, введите название продукта в формате /log_food <название продукта>"
        )
        return

    await message.answer("Получаю данные о продукте...")
    food_info = await get_food_info(command_args)
    await state.update_data(food_type=command_args)

    if food_info is None:
        await message.answer("У меня нет данных об этом продукте. Пожалуйста, введите калорийность продукта на 100 г.")
        await state.update_data(calories_100g=None)
    else:
        await state.update_data(calories_100g=food_info['calories'])
        await message.answer(f"Калорийность продукта на 100 г - {food_info['calories']} ккал. Сколько Вы употребили в г (мл)?")
    await state.set_state(FoodState.amount)

@router.message(FoodState.amount)
async def log_food(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()

    #Ввод калорийности еды в случае отсутствия продукта в базе
    if data['calories_100g'] is None:
        try:
            await state.update_data(calories_100g=int(message.text))
        except ValueError:
            await message.answer("Пожалуйста, введите число")
            return
        await message.answer("Введите количество употребленного продукта в г (мл)")
        return #Остаемся в этом состоянии, но с другим контекстом
    else:
        try:
            food_amount = int(message.text)
        except ValueError:
            await message.answer("Пожалуйста, введите число")
            return

        consumed_calories = data['calories_100g'] * food_amount / 100 #Расчет количества потребленных калорий

        #Логирование калорий
        user_data = await db.get_user(message.from_user.id)
        logged_calories = consumed_calories + user_data['logged_calories'] #Суммируем общее количество потребленных калорий
        await db.log_calories(logged_calories)

        await message.answer(
            f"Записано: {consumed_calories} ккал\n"
            f"Всего потреблено калорий: {logged_calories} ккал\n"
        )

        await state.clear()

@router.message(Command('log_workout'))
async def cmd_log_workout(message: Message, command: CommandObject, db: Database):
    #Проверка наличия профиля
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("Сначала настройте профиль: /set_profile")
        return

    #Проверка введенных аргументов
    available_workout_types = ('бег', 'ходьба', 'велосипед', 'плавание', 'йога', 'силовая', 'кардио', 'танцы', 'футбол', 'баскетбол')
    command_args: str = command.args
    try:
        workout_type, workout_duration = command_args.split(" ")
    except:
        await message.answer(
            "Пожалуйста, введите тип и время тренировки в минутах через пробел в формате:\n"
            "/log_workout <тип тренировки> <время>\n"
            f"Доступные типы тренировок: {', '.join(available_workout_types)}"
        )
        return
    
    try:
        workout_duration = int(workout_duration)
    except ValueError:
        await message.answer("Пожалуйста, введите время тренировки в корректном формате (количество минут)")
        return
    
    burned_calories = calculate_workout_calories(workout_type, workout_duration, user_data['weight'])
    burned_calories_total = burned_calories + user_data['burned_calories'] #Суммируем общее количество сожженных калорий
    
    # Рассчитываем дополнительную воду
    extra_water = int((int(workout_duration) / 30) * 200)
    new_water_goal = user_data['water_goal'] + extra_water

    await db.log_workout(burned_calories_total, new_water_goal)

    await message.answer(
        f"{workout_type.capitalize()} {workout_duration} минут - сожжено {burned_calories:.0f} ккал\n"
        f"Дополнительно: выпейте {extra_water} мл воды\n"
        )

@router.message(Command('check_progress'))
async def cmd_check_progress(message: Message, command: CommandObject, db: Database):
    #Проверка наличия профиля
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("Сначала настройте профиль: /set_profile")
        return

    remaining_water = user_data['water_goal'] - user_data['logged_water']
    remaining_calories = user_data['calorie_goal'] - user_data['logged_calories'] + user_data['burned_calories']

    if remaining_water > 0:
        water_msg = f"- Осталось: {remaining_water} мл."
    elif remaining_water < 0:
        water_msg = f"- Вы выпили на {-remaining_water} мл больше цели."
    else:
        water_msg = "- ✅Цель выполнена!"

    if remaining_calories > 0:
        calories_msg = f"- Осталось: {remaining_calories} ккал."
    elif remaining_calories < 0:
        calories_msg = f"- Вы употребили на {-remaining_calories} ккал больше цели."
    else:
        calories_msg = "- ✅Цель выполнена!"
    
    await message.answer(
        "📊 Прогресс:\n"
        "Вода:\n"
        f"- Выпито: {user_data['logged_water']} мл из {user_data['water_goal']} мл.\n" +
        water_msg +
        "\n\nКалории:\n"
        f"- Потреблено: {user_data['logged_calories']} ккал из {user_data['calorie_goal']} ккал.\n"
        f"- Сожжено: {user_data['burned_calories']} ккал.\n" +
        calories_msg
        )

def setup_handlers(dp):
    dp.include_router(router)


    
    

    