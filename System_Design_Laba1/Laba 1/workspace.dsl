workspace {
    name "EventBOOST"
    description "Сайт конференции"

    model {
        user = person "Пользователь"

        EventBOOST = softwareSystem "EventBOOST"{
            description "Система для создания онлайн мероприятий"

            web = container "Веб-сприложение" {
                description "Позволяет пользователю через браузер взаимодействовать с сервисом через браузер"

                technology "JavaScript"

            } 

            APIGateway = container "API Gateway" {
                description "Обеспечивает доступ к бизнес-логике"
            }

            userService = container "Управление пользователями" {
                description "Сервис управления пользователями"
                technology "Spring"

            }

            doklad = container "Взаимодействие с докладами" {
                description "Создание/работа докладов"
                technology "Spring"

            }

            conference = container "Взаимодействие с конференциями" {
                description "Старт/конец конференций и добавление информации"

                technology "Spring"
            }

            usersData = container "База данный пользователей" {
                description "Добавление/удаление информации пользователей"
                technology "PostgreSQL"

            }

            dokladDataBase = container "База данных докладов" {
                description "Хранение информации о докладах"
                technology "PostgreSQL"

            }

            conferenceDataBase = container "База данных конференций" {
                description "Хранение информации о конферениях"
            }

            user -> web "Запрос пользователя и его взаимодействие"
            web -> APIGateway "API запросы"
            APIGateway -> userService
            APIGateway -> doklad
            APIGateway -> conference

            userService -> usersData "Запись и чтение инормации пользователей" "JDBC"
            doklad -> dokladDataBase "Запись и чтение докладов"
            conference -> conferenceDataBase "Запись и чтение конференций"

            // Создание пользователей
            user -> web "Создание нового пользователя"
            web -> APIGateway
            APIGateway -> userService "Запрос на нужный Сервис"
            userService -> usersData

            // Поиск пользователя по логину
            user -> web "Поиск пользователя по логину"
            web -> APIGateway
            APIGateway -> userService
            userService -> usersData "SELECT * FROM users WHERE login = {login}"

            // Поиск пользователя по маске имени и фамилии
            user -> web "Поиск пользователя по маске имени и фамилии"
            web -> APIGateway 
            APIGateway -> userService
            userService -> usersData "SELECT * FROM isers WHERE name LIKE {name} AND surname LIKE {surname}"

            // Создание доклада
            user -> web "Создание доклада"
            web -> APIGateway "Запрос на создание доклада"
            APIGateway -> doklad
            doklad -> dokladDataBase "ISERT INTO doklad"

            // Получение списка всех докладов
            user -> web "Получение списка всех докладов"
            web -> APIGateway "Запрос на получение списка докладов из сервиса"
            APIGateway -> doklad
            doklad -> dokladDataBase "SELECT * FROM doklad"

            // Добавление доклада в конференцию
            user -> web "Добавление доклада в конференцию"
            web -> APIGateway "Запрос на Добавление доклада в конференцию"
            APIGateway -> doklad
            doklad -> dokladDataBase "Select * FROM doklad WHERE name = {name}"
            dokladDataBase -> conference
            conference -> conferenceDataBase "INSERT INTO conference"

            // Получение списка докладов в конференции
            user -> web "Получение списка докладов в конференции"
            web -> APIGateway "Запрос на получение списка докладов в конференции"
            APIGateway -> conference
            conference -> conferenceDataBase "SELECT doklad FROM conference"

        }


    }

    views {
        themes default

        systemContext EventBOOST {
            include *
            autoLayout
        }

        container EventBOOST {
            include *
            autoLayout lr
        }

        dynamic EventBOOST {
            user -> EventBOOST.web "Создание нового пользователя"
            EventBOOST.web -> EventBOOST.APIGateway
            EventBOOST.APIGateway -> EventBOOST.userService
            EventBOOST.userService -> EventBOOST.usersData
            autoLayout lr
        }
        
        dynamic EventBOOST {
            user -> EventBOOST.web
            EventBOOST.web -> EventBOOST.APIGateway
            EventBOOST.APIGateway -> EventBOOST.userService
            EventBOOST.userService -> EventBOOST.usersData "SELECT * FROM users WHERE login = {login}"
            autoLayout lr
        }

        dynamic EventBOOST {
            user -> EventBOOST.web "Поиск пользователя по логину"
            EventBOOST.web -> EventBOOST.APIGateway
            EventBOOST.APIGateway -> EventBOOST.userService
            EventBOOST.userService -> EventBOOST.usersData "SELECT * FROM users WHERE login = {login}"
            autoLayout lr
        }

        dynamic EventBOOST {
            user -> EventBOOST.web "Поиск пользователя по маске имени и фамилии"
            EventBOOST.web -> EventBOOST.APIGateway 
            EventBOOST.APIGateway -> EventBOOST.userService
            EventBOOST.userService -> EventBOOST.usersData "SELECT * FROM isers WHERE name LIKE {name} AND surname LIKE {surname}"
            autoLayout lr
        }

        dynamic EventBOOST {
            user -> EventBOOST.web "Создание доклада"
            EventBOOST.web -> EventBOOST.APIGateway "Запрос на создание доклада"
            EventBOOST.APIGateway -> EventBOOST.doklad
            EventBOOST.doklad -> EventBOOST.dokladDataBase "ISERT INTO doklad"
            autoLayout lr
        }

        container EventBOOST {
            include *
            autoLayout lr
        }
        
        
    }
}