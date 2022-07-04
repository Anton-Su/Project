import datetime
import logging
import pytz
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
import pymorphy2
import sqlite3
from time import time
import json
from random import choice

con = sqlite3.connect("antimat.db", check_same_thread=False)
cur = con.cursor()

cur.execute("""Update Users
            SET TASKS = '[]'""")
con.commit()
mat_noun = []
mat_verv = []
padeshi = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']
chicla = ['sing', 'plur']
itog = []
result = cur.execute("""SELECT Noun FROM Antimat""").fetchall()
for elem in result:
    mat_noun.append(elem[0])
result = cur.execute("""SELECT Verb FROM Antimat""").fetchall()
for elem in result:
    if elem[0]:
        mat_verv.append(elem[0])
con.close()
morph = pymorphy2.MorphAnalyzer()
hello = [['/help', '/info']]
reply_keyboard = [['/music', '/clock'],
                  ['/info', '/timer']]
reply_keyboard2 = [['Неплохо', 'Хорошо'],
                   ['Нормально', 'Плохо']]
mus = [open('привет_войска.mp3', 'rb'), open('last breath.mp3', 'rb'), open('калинка.mp3', 'rb'),
       open('ванпанч.mp3', 'rb'), open('хит.mp3', 'rb'), open('бизарные богатыри.mp3', 'rb'),
       open('дикий конь.mp3', 'rb'), open('непонятка.mp3', 'rb')]
rep = ['Неплохо', 'Хорошо', 'Нормально', 'Плохо']
TOKEN = "5326929599:AAEyIH_mkjXQ-22UfLLLYUGZj59DrzbGQjw"
updater = Updater(TOKEN, use_context=True)
markup = telegram.ReplyKeyboardMarkup(hello, one_time_keyboard=False)
markup2 = telegram.ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
markup3 = telegram.ReplyKeyboardMarkup(reply_keyboard2, one_time_keyboard=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


def human_read_format(size, i=0):
    d = ['Б', 'КБ', 'МБ', 'ГБ']
    s = size
    while size >= 1024 and i < 3:
        size = round(size / 1024)
        i += 1
    return f'{size}{d[i]} ({s}) б'


def music(update, context, n=0):
    work(update, context)
    try:
        context.bot.send_audio(chat_id=update.message.chat.id, audio=choice(mus))
        update.message.reply_text(choice(['Музыка разная бывает, попробуй послушать эту...',
                                          'Это моя любимая',
                                          'Эту я бы слушала всегда']))
    except telegram.error.BadRequest:
        if n < 10:
            music(update, context, n+1)
            return True
        update.message.reply_text('Не удалось отправить, вот')


def podshet(chast, first, second, third):
    for i in first:
        count = 0
        try:
            res = morph.parse(i)[count]
            while chast not in res.tag:
                res = morph.parse(i)[count]
                count += 1
        except IndexError:
            itog.append(i)
            continue
        for chiclo in second:
            for pades in third:
                wor = res.inflect({chiclo, pades}).word
                itog.append(wor)
    return itog


def change(update, context, result):
    karma = result[1]
    con = sqlite3.connect("antimat.db", check_same_thread=False)
    cur = con.cursor()
    cur.execute(f"""update Users
                       set karma = {karma}
                       WHERE id like {update.message.from_user.id} and confa like {update.message.chat.id}""")
    con.commit()
    cur.execute('UPDATE Users SET tasks = ? WHERE id = ? and confa = ?',
                (json.dumps(result[0]), update.message.from_user.id, update.message.chat.id,))
    con.commit()
    con.close()


def talk(update, context):
    if obrabotchic(update, context):
        result = work(update, context)
        itog = podshet('NOUN', mat_noun, padeshi, chicla)
        itog = set(itog)
        itog = list(itog)
        itog.extend(mat_verv)
        if any(i in update.message.text.lower() for i in itog):
            result[1] -= 20
            update.message.reply_text('Так-так, нарушаем порядок!!!')
            try:
                s = restrict_or_promote(update, context, result[1])
                if not s:
                    update.message.reply_text(f'Твоя karma равна {result[1]}, потом не жалей о своих поступках')
            except Exception:
                update.message.reply_text(
                    f'К слову, зачем ты нарушаешь, если знаешь, что выйдешь безнаказанным?')
                result[1] += 20
            context.bot.deleteMessage(chat_id=update.message.chat_id, message_id=update.message.message_id)
            change(update, context, result)
            return True
        if 'beta' in update.message.text.lower() or 'бета' in update.message.text.lower():
            update.message.reply_text(
                choice(['К слову, о нас...Если я тебе так интересно, напиши моё имя, как команду. Ты же её знаешь?',
                        'Ты думаешь, весело не понимать, что тебе пишет собеседник? Напиши /моё имя, сложно?',
                        'Я молчалива? Возможно... но /моё имя исправит этот момент']))


def beta(update, context):
    work(update, context)
    update.message.reply_text(choice(
        ['О, я удивлена. Хотя, не думаю, что и ты тоже. Такая вот несчастная судьба у ботов',
         'Хочешь сказать, тебя заинтересовала какая - то программа?']))
    update.message.reply_text('Давай пообщаемся? Ты сможешь прервать данный опрос командой /close')
    update.message.reply_text(f'Как ты сейчас себя чувствуешь?', reply_markup=markup3)
    return 1


def audio(update, context):
    update.message.reply_text(
        f'Длина твоего сообщения составила {update.message.voice.duration} cекунд, а вес '
        f'получился под {human_read_format(update.message.voice.file_size)}')
    update.message.reply_text('Я пока не умею обрабатывать голосовые, так что '
                              'найди себе кого - то (опционально), моя тебе вряд ли понравится)')
    au = open('спидран.ogg', 'rb')
    context.bot.send_audio(chat_id=update.message.chat_id, audio=au)


def al(update, context):
    if obrabotchic(update, context):
        update.message.reply_text(
            choice(['Делать больше нечего?', 'Пользователи в последнее время какие - то чересчур странные',
                    '"А что будет, если" - ничего не будет, бета не твоя слуга',
                    'Я подумала тебе не отвечать, но всё же ответила']))


def demand(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    people = context.bot.getChatMember(chat_id=chat_id, user_id=user_id)
    if people.status == 'creator':
        try:
            update.message.text = update.message.text.split('!')
            time = int(update.message.text[-1]) if len(update.message.text) == 3 and int(
                update.message.text[-1]) > 30 else 86400
            if update.message.text[0][1:].lower() == 'ban':
                ban(update, context, chat_id, update.message.text[1], time)
            elif update.message.text[0][1:].lower() == 'mute':
                restrict(update, context, chat_id, update.message.text[1], time)
            elif update.message.text[0][1:].lower() == 'unmute':
                restrict(update, context, chat_id, update.message.text[1], time, True, True, True, True, True, True,
                         True, True)
            elif update.message.text[0][1:].lower() == 'promote':
                promote(update, context, chat_id, update.message.text[1])
            elif update.message.text[0][1:].lower() == 'unban':
                unban(update, context, chat_id, update.message.text[1])
            update.message.reply_text('Вердикт вынесен')
            photo = open('молоток.jpg', 'rb')
            context.bot.sendPhoto(chat_id=chat_id, photo=photo)
            return True
        except Exception:
            update.message.reply_text(
                'Инструкция: /ban!(mute, unmute, unban, promote)!<id>!<время(сек, по умолчанию 24 часа(не менее 30 с)>')
            update.message.reply_text(
                'Пример: /unmute!12345678999!45')


def restrict_or_promote(update, context, result):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    if result <= -200:
        update.message.reply_text('Кто - то ОТВРАТИТЕЛЬНО себя ведёт! Таким не место в нашем ряду!')
        photo = open('remove.png', 'rb')
        context.bot.sendPhoto(chat_id=chat_id, photo=photo)
        ban(update, context, chat_id, user_id)
        return True
    if result == 0:
        update.message.reply_text('Кто - то ПЛОХО себя ведёт! Возможно, денёк молчания научит тебя манерам')
        restrict(update, context, chat_id, user_id)
        photo = open('mute.jpg', 'rb')
        context.bot.sendPhoto(chat_id=chat_id, photo=photo)
        return True


def ban(update, context, сhat_id, user_id, timee=86400):
    context.bot.ban_chat_member(
        chat_id=сhat_id,
        user_id=user_id,
        until_date=time() + timee,
        revoke_messages=True)


def unban(update, context, chat_id, user_id):
    context.bot.unban_chat_member(chat_id=chat_id,
                                  user_id=user_id, only_if_banned=True)


def promote(update, context, chat_id, user_id):
    context.bot.promoteChatMember(chat_id=chat_id, user_id=user_id, is_anonymous=True,
                                  can_manage_chat=False,
                                  can_post_messages=True,
                                  can_edit_messages=True,
                                  can_delete_messages=True,
                                  can_restrict_members=False,
                                  can_promote_members=False,
                                  can_change_info=True,
                                  can_invite_users=True,
                                  can_pin_messages=True)


def restrict(update, context, chat_id, user_id, timee=86400, can_send_messages=False,
             can_send_media_messages=False, can_send_polls=False, can_send_other_messages=False,
             can_add_web_page_previews=False, can_change_info=False, can_invite_users=False,
             can_pin_messages=False):
    t = telegram.ChatPermissions(can_send_messages=can_send_messages, can_send_media_messages=can_send_media_messages,
                                 can_send_polls=can_send_polls, can_send_other_messages=can_send_other_messages,
                                 can_add_web_page_previews=can_add_web_page_previews,
                                 can_change_info=can_change_info, can_invite_users=can_invite_users,
                                 can_pin_messages=can_pin_messages)
    context.bot.restrict_chat_member(chat_id, user_id, permissions=t, until_date=time() + timee)


def close(update, context):
    update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def first_response(update, context):
    first = update.message.text.strip()
    if first in rep:
        update.message.reply_text(
            choice(['Как шаблонно, пойду в спячку. Меня не ждать(', '"User" действительно не понимает, '
                                                                    'что так отвечать скучно? Я обиделась(']))
        return ConversationHandler.END
    update.message.reply_text('Вот оно как... Я не умею понимать, не умею чувствовать, '
                              f'поэтому просто скопирую твоё настроение. Я чувствую себя тоже {first.lower()}')
    update.message.reply_text('А где ты живёшь?')
    return 2


def second_response(update, context):
    update.message.reply_text(
        choice([f'Мне всегда говорили, что "{update.message.text.strip()}" неплохой город', 'А я живу на одном сервере'
                                                                                            ' "pythoneverywhere"']))
    update.message.reply_text(
        f'И я могла бы проверить этот город на реальное существование, но я тебе верю!')
    update.message.reply_text('Я знаю кое - что поинтереснее! Поиграем в акинатора, но у тебя всего одна попытка! '
                              'Не ответишь - мут на день, а если угадаешь - ты не угадаешь, хе')
    update.message.reply_text('Персонаж, которому сама королева не дала умереть вовреки воли его автора. Кто это?')
    return 3


def third_response(update, context):
    if 'шерлок' in update.message.text.lower():
        photo = open('correct.jpg', 'rb')
        context.bot.sendPhoto(chat_id=update.message.chat.id, photo=photo)
        update.message.reply_text("А ты удивительный...")
        try:
            promote(update, context, chat_id=update.message.chat.id, user_id=update.message.from_user.id)
        except telegram.error.BadRequest:
            update.message.reply_text("Не могу повысить тебя, так как ты уже на вершине... личных сообщений")
        return ConversationHandler.END
    update.message.reply_text("День не так уж и много для осознания своих ошибок, не так ли?")
    try:
        update.message.reply_text("Ты бы видел себя user) Маленький ещё)")
        restrict(update, context, chat_id=update.message.chat.id, user_id=update.message.from_user.id)
    except telegram.error.BadRequest:
        update.message.reply_text("Сыграем в молчанку хотя бы на словах?")
    return ConversationHandler.END




def help(update, context):
    work(update, context)
    photo = open('help.jpg', 'rb')
    update.message.reply_text('Забыл команды? Beta написала их внизу, чтобы ты не искал долго')
    context.bot.sendPhoto(chat_id=update.message.chat.id, photo=photo)
    update.message.reply_text('/site - ссылка на мечты')
    update.message.reply_text('/work - процесс синхронизации')
    update.message.reply_text('/info - данные профиля')
    update.message.reply_text('/music - послушать музыку')
    update.message.reply_text('/timer - таймер')
    update.message.reply_text('/stop - остановка')
    update.message.reply_text('/clock - завести будильник', reply_markup=markup2)


def site(update, context):
    work(update, context)
    photo = open('забавно.jpeg', 'rb')
    context.bot.sendPhoto(chat_id=update.message.chat.id, photo=photo)
    update.message.reply_text('Это - уголок моей мечты. '
                              'Не видно, наверное, но почему нет?')


def obrabotchic(update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    people = context.bot.getChatMember(chat_id=chat_id, user_id=user_id)
    return not people.user.is_bot


def work(update, context):
    con = sqlite3.connect("antimat.db", check_same_thread=False)
    cur = con.cursor()
    result = cur.execute("""SELECT id, confa FROM Users""").fetchall()
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    if (user_id, chat_id) not in result:
        update.message.reply_text('Мы не нашли записей того, что вы были в системе')
        update.message.reply_text('Создаю ваш профиль...')
        update.message.reply_text('Рекомендую воспользоваться командой "music"')
        cur.execute(f'''
                        INSERT INTO Users (id, confa, karma, lvl)
                        VALUES
                        ({user_id}, {chat_id}, 100, 0)
                        ''')

        con.commit()
        file = open('Не абузь систему.docx', 'rb')
        p = context.bot.send_document(chat_id=update.message.chat_id, document=file)
        context.bot.pinChatMessage(message_id=p.message_id, chat_id=update.message.chat.id)
        update.message.reply_text(f'Успешная регистрация, {user_id}, теперь ознакомься с правилами',
                                  reply_markup=markup2)
    result = cur.execute(f"""SELECT tasks, karma, lvl FROM Users
            Where id={user_id} and confa={chat_id}""").fetchall()
    cur.close()
    result = result[0]
    result = list(result)
    if not result[0]:
        result[0] = []
    else:
        result[0] = json.loads(result[0])
    current_jobs = context.job_queue.jobs()
    spisok = []
    for i in current_jobs:
        spisok.append(i.name)
    new_spisok = []
    for i in range(len(result[0])):
        if result[0][i] in spisok:
            new_spisok.append(result[0][i])
    result[0] = new_spisok
    return result


def info(update, context):
    result = work(update, context)
    update.message.reply_text(f'Имя (ваше ID) - {update.message.from_user.id}')
    update.message.reply_text(f'Карма - {result[1]}')
    update.message.reply_text(f'Уровень - {result[2]}')
    if len(result[0]):
        update.message.reply_text(
            f'Текущее количество таймеров {len(result[0])} c их названиями {[i for i in result[0]]}')
    else:
        update.message.reply_text('Таймеры вне зоны досигаемости. /timer or /clock? Я ЗА!')
    return result


def start(update, context):
    update.message.reply_text(choice(['Привет, user. Ты по делу или просто так "заскочить"?',
                                      'Добро пожаловать к нам снова ... или в первый раз?',
                                      'Знакомство - всегда хорошо. Для "Беты" точно. ']))
    photo = open('hello.jpg', 'rb')
    context.bot.sendPhoto(chat_id=update.message.chat.id, photo=photo)
    update.message.reply_text('Не двигайся, user. Я "зарегистрирую" тебя, если ты, конечно, ещё не в моей базе данных',
                              reply_markup=markup)
    work(update, context)


def stop(update, context):
    update.message.text = update.message.text.split('!')
    t = work(update, context)
    if len(update.message.text) == 1:
        update.message.reply_text('Использование: /stop!<название задачи. Если хочется отменить всё, '
                                  'используйте точку, но учтите, что таймеры ДРУГИХ людей вы не сможете остановить. '
                                  'Исключение - вы админ группового чата>')
        update.message.reply_text('Пример: /stop!задачаномервосемнадцать')
        update.message.reply_text('Пример2: /stop!.')
        return True
    job_removed = remove_job_if_exists(update, context, update.message.text[1], t)
    text = 'Устранила "повторяшку!"' if job_removed else \
        'Бета против. Все ваши таймеры, если и были, то уже остановились'
    update.message.reply_text(text)


def timer_(context):
    context.bot.send_message(chat_id=context.job.context,
                             text=choice([f'I am here, user. Я пришла тебе напомнить о задаче "{context.job.name}"',
                                          f'{context.job.name}? УЖЕ? Ну вот, заново считать',
                                          f'ЭЙ, user, я тебя не отвлекаю, но... {context.job.name} уже здесь!']))


def timer(update, context):
    chat_id = update.message.chat_id
    result = work(update, context)
    try:
        t = update.message.text.split()
        current_jobs = context.job_queue.jobs()
        spisok = []
        b = str(t[3]) if len(t) == 4 else str(f'Таймер{len(spisok) + 1}')
        for i in current_jobs:
            spisok.append(i.name)
        while b in spisok:
            b = b + choice(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '_'])
        context.job_queue.run_repeating(timer_, interval=int(t[1]), first=int(t[2]), context=chat_id,
                                        name=b)
        result[0].append(b)
        update.message.reply_text('Завела вашего попугая')
        change(update, context, result)
    except (IndexError, ValueError):
        update.message.reply_text(
            'Использование: /timer <интервал> <первый запуск> <описаниебезпробелов>. Всё в секундах')
        update.message.reply_text('Пример: /timer 50 2 скука_смертная')
        return True


def remove_job_if_exists(update, context, who, work):
    current_jobs = context.job_queue.jobs()
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    people = context.bot.getChatMember(chat_id=chat_id, user_id=user_id)
    work2 = []
    number = False
    if people.status == 'creator' and chat_id != user_id:
        con = sqlite3.connect("antimat.db", check_same_thread=False)
        cur = con.cursor()
        work_ = cur.execute(f"""SELECT tasks FROM Users
        Where id not like {user_id} and confa like {chat_id}""").fetchall()
        con.close()
        for i in work_:
            work2.extend((json.loads(i[0])))
    for job in current_jobs:
        if who == '.' and (job.name in work[0] or job.name in work2):
            job.schedule_removal()
            number = True
            if job.name in work[0] and not work2:
                del work[0][work[0].index(job.name)]
            else:
                update.message.reply_text(f'Администратор отменил задачу {job.name}')
        elif job.name == who and (who in work[0] or who in work2):
            job.schedule_removal()
            if who in work[0] and not work2:
                del work[0][work[0].index(who)]
            else:
                update.message.reply_text(f'Администратор отменил задачу {job.name}')
            change(update, context, work)
            return True
    if number:
        change(update, context, work)
        return number


def clock(update, context):
    t = update.message.text.split()
    result = work(update, context)
    try:
        r = t[1].split(':')
        t[2] = tuple(t[2])
        current_jobs = context.job_queue.jobs()
        spisok = []
        b = str(t[3]) if len(t) == 4 else str(f'Напоминалка{len(spisok) + 1}')
        for i in current_jobs:
            spisok.append(i.name)
        while b in spisok:
            b = b + choice(['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '_'])
        context.job_queue.run_daily(timer_,
                                    datetime.time(hour=int(r[0]), minute=int(r[1]), second=int(r[2]),
                                                  tzinfo=pytz.timezone('Europe/Moscow')),
                                    days=t[2], context=update.message.chat_id,
                                    name=b)
        result[0].append(b)
        update.message.reply_text('Завела ваш будильник')
        change(update, context, result)
    except (IndexError, ValueError):
        update.message.reply_text(
            'Использование: /clock <ч:м:с> <0 - понедельник, 6 - воскресенье 012 - сочетание> <описаниебезпробелов>')
        update.message.reply_text(
            'Пример: /clock 10:10:10 012 ещё_один_таймер')
        update.message.reply_text(
            'Расшифровка: Каждый понедельник, вторник и среду в 10 часов 10 минут '
            '10 секунд будет звонить "ещё_один_таймер"')


def main():
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('beta', beta)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, second_response)],
            3: [MessageHandler(Filters.text & ~Filters.command, third_response)]
        },

        fallbacks=[CommandHandler('close', close)]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start, pass_job_queue=True))
    dp.add_handler(CommandHandler("help", help, pass_job_queue=True))
    dp.add_handler(CommandHandler("music", music, pass_job_queue=True))
    dp.add_handler(CommandHandler("site", site, pass_job_queue=True))
    dp.add_handler(CommandHandler("info", info, pass_job_queue=True))
    dp.add_handler(CommandHandler("timer", timer, pass_job_queue=True))
    dp.add_handler(CommandHandler("stop", stop, pass_job_queue=True))
    dp.add_handler(CommandHandler("clock", clock, pass_job_queue=True))
    dp.add_handler(CommandHandler("ban", demand, pass_job_queue=True))
    dp.add_handler(CommandHandler("mute", demand, pass_job_queue=True))
    dp.add_handler(CommandHandler("unmute", demand, pass_job_queue=True))
    dp.add_handler(CommandHandler("promote", demand, pass_job_queue=True))
    dp.add_handler(CommandHandler("unban", demand, pass_job_queue=True))
    text_handler = MessageHandler(Filters.text, talk)
    text_handler1 = MessageHandler(Filters.voice, audio)
    text_handler2 = MessageHandler(Filters.all, al)
    dp.add_handler(text_handler)
    dp.add_handler(text_handler1)
    dp.add_handler(text_handler2)
    updater.start_polling()
    updater.idle()

main()
