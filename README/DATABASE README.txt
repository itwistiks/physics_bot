--------------------------------------------------------------------------------------------------
Возможные дополнения
--------------------------------------------------------------------------------------------------


*? Важное дополнение для анализа ошибок в UserAnswers (новая таблица). 
	UserAnswers
	├── id (PK, SERIAL)                 # Уникальный ID записи (автоинкремент)
	├── user_id (FK → Users)            # Связь с пользователем:
	│                                   # ON DELETE CASCADE - если удалим пользователя, его ответы удалятся
	├── task_id (FK → Tasks)            # Связь с задачей:
	│                                   # ON DELETE SET NULL - если задачу удалят, связь сохранится без ошибок
	├── selected_answer (TEXT/JSONB)    # Данные ответа:
	│                                   # - Для тестов: "Вариант 2"
	│                                   # - Для расчётных задач: "F=ma"
	│                                   # - Для множественного выбора: ["A", "C"] (в JSONB)
	├── is_correct (BOOLEAN)            # Статус правильности:
	│                                   # TRUE - верный ответ
	│                                   # FALSE - ошибка
	├── response_time (INTERVAL)        # Затраченное время:
	│                                   # Формат: '00:01:45' (1 минута 45 секунд)
	│                                   # NULL - если таймер не использовался
	└── timestamp (TIMESTAMP)           # Момент отправки ответа:
	                                    # DEFAULT CURRENT_TIMESTAMP
	                                    # Индекс для анализа активности по датам


--------------------------------------------------------------------------------------------------
Базы проекта
--------------------------------------------------------------------------------------------------


Tasks database
│
├── Tasks content
│   ├── id (PK, SERIAL)                 # Уникальный ID задачи
│   ├── type_number (INT)               # Номер типа задания в ОГЭ (1-25)
│   ├── topic_id (FK → Topics)          # Связь с темой
│   ├── subtopic_id (FK → Subtopics)    # Связь с подтемой
│   ├── part_number (ENUM)				# Первая или вторая часть ОГЭ
│   ├── complexity (ENUM)               # 'basic', 'advanced', 'high'
│   ├── task_content (JSONB)            # Контент задачи в формате: {"text": "Текст задачи", "image": "url/to/image.jpg"}
│   ├── correct_answer (TEXT/JSONB)     # Правильный ответ (вариант или формула)
│   ├── answer_options (JSONB)          # Варианты ответов: ["Да", "Нет", "Не знаю"]
│   ├── theory_id (FK → Theories)       # Связь с теорией (если есть)
│   └── video_analysis_url (TEXT)       # Ссылка на видеоразбор (NULL для basic или advanced)
│
├── Theories
│   ├── id (PK, SERIAL)                 # Уникальный ID теории
│   ├── topic_id (FK → Topics)          # Связь с темой
│   ├── subtopic_id (FK → Subtopics)    # Связь с подтемой
│   ├── complexity (ENUM)               # 'basic', 'advanced', 'high'
│   ├── content (TEXT)                  # Теоретический текст (Markdown-форматирование)
│   └── examples (JSONB)                # Примеры задач в формате: [{"task": "Текст задачи", "solution": "Решение"}]
│
├── Topics
│    ├── id (PK, SERIAL)                # Уникальный идентификатор темы
│    ├── name (VARCHAR)                 # Название темы на английском (для кода)
│    └── title_ru (VARCHAR)             # Название темы на русском (для отображения)
│  
└── Subtopics
    ├── id (PK, SERIAL)                 # Уникальный идентификатор подтемы
    ├── topic_id (FK → Topics)          # Связь с родительской темой
    ├── name (VARCHAR)                  # Название подтемы (англ. для кода)
    └── title_ru (VARCHAR)              # Название на русском
  





Users database
├── Users  
│   ├── id (PK)                          # Уникальный ID пользователя
│   ├── username (TEXT)					 # Ник в тг
│   ├── registration_date (DATE)         # Дата регистрации (TIMESTAMP)
│   ├── status (ENUM)                  	 # 'no_sub', 'sub', 'pro_sub', 'teacher', 'moderator', 'admin'
│   ├── phone (NULLABLE)		 		 # NULL, если нет подписки 
│   ├── city (NULLABLE)		 	 		 # NULL, если нет подписки 
│   └── last_interaction_time (DATE)  	 # Последняя активность (для напоминаний)
│
├── UserStats  
│   ├── user_id (FK → Users)  			 # Связь с пользователем
│   ├── subtopics_stats (JSONB)		     # Список подтем с количеством правильных и неправильных ответов в виде 
│	│					# {"subtopic_id": {"Количество верных ответов"m "Количество неверных ответов"}} например {"1": {"correct": 5, "wrong": 2},"5": {"correct": 3, "wrong": 4}}
│   ├── correct_answers (INT)            # Число верных ответов
│   ├── total_attempts (INT)         	 # Всего попыток
│   └── percentage (FLOAT)               # Процент верных: correct_answers/total_attempts*100
│  
├── UserProgress  
│   ├── user_id (FK → Users)   		 	 # Связь с пользователем
│   ├── daily_record (INT)               # Рекорд за день (например, 20 задач)
│   ├── weekly_points (INT)              # Очки за неделю (для геймификации)
│   ├── total_points  (INT)              # Общие очки (прогресс)
│   ├── current_streak (INT)		 	 # Текущая серия дней с решением задач
│   └── last_active_day (DATE)           # Для проверки ежедневных достижений
│
└── UserAchievements
    ├── user_id (FK → Users)  			 # Связь с пользователем
    ├── achievement_id (FK → Achievements)  # Связь с достижением
    ├── unlocked_at (TIMESTAMP)      	 # Дата и время получения в случае прогреса 100%
    └── progress (INT)               	 # Прогресс (например, 7/10 задач) 






Achievements database
├── id (PK, SERIAL)          		# Уникальный ID достижения  
├── name (VARCHAR)           		# Название (например, "Новичок")
├── description (TEXT)       		# Описание для пользователя
├── reward_points (INT)			    # Количество опыта за ачивку
└── condition (TEXT)	         	# Условие на SQL/Python-логику (пример ниже) 
					# Поле condition хранит логику проверки достижения в формате, который может интерпретировать бот. Например:
					#  - solved_tasks >= 10 — решено 10+ задач.
					#  - correct_percentage > 80 AND topic_id = 3 — 80%+ правильных ответов по электричеству
					# INSERT INTO Achievements (name, description, condition, icon_url) VALUES
					#   ('Новичок', 'Решить первую задачу', 'solved_tasks >= 1', 'icons/newbie.png'),
					#   ('Эксперт по механике', 'Решить 20 задач по механике', 'solved_tasks WHERE topic_id = 1 >= 20', 'icons/mech_expert.png'),
					#   ('Стрикер', 'Решать задачи 5 дней подряд', 'daily_streak >= 5', 'icons/streak.png'); 


Reminder database
├── id (PK, SERIAL)				# Уникальный ID сообщения о напоминании
├── date (DATE)					# Дата для случаа праздника
├── reminder_type (ENUM)		# Тип напоминания: 'inactive', 'holiday', 'promo'
└── text (TEXT)					# Текст напоминания


--------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------------