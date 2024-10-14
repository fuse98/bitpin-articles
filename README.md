# BitPin Articles

This is a simple web service for serving articles and enabling users to rate those articles.
The web service includes a spam rate detection feature.

## Running Locally

1. Clone project

2. Create python virtual environment and activate it
```
python3 -m venv venv
source venv/bin/activate
```
3. Install requirments

```
pip install -r requirements.txt
```
4. export environment variables listed in env-template file or in configuration section below

5. Make sure postgres db is running and the DB with the correct name exists in it

6. Make sure redis is running

7. Run migrations
```
cd src
python manage.py migrate
```

8. Run server
```
cd src
python manage.py runserver
```

9. For spam detection to work properly run celery beat and celery worker
(The following command runs both. Only suitable for development environments)
```
celery -A core  worker -B
```

## Runing Test

1. Make sure db is runing
2. Make sure environment has the requirments
3. Make sure all configs are in place
4. run this command:
```
cd src
python manage.py test
```

## APIs Overview

### Authentication

Token based authentication is used in this project. 

The retrived token from login API should be put in header like this:
```
Authorization: TOKEN <retrived token>
```

### Endpoints

#### Users App

**POST /users/register**

- **Description**: Register new user
- **Authentication**: Not required
- **Body**: 
  - `username`
  - `email` (optional)
  - `password`
  - `password_confirm`

- **Example Response**:
  ```json
    {
        "message": "User created successfully",
        "user": {
            "username": "username",
            "email": "email@example.com"
        }
    }
  ```

**POST /users/login**

- **Description**: Authenticate user
- **Authentication**: Not required
- **Body**: 
  - `username`
  - `password`

- **Example Response**:
  ```json
    {
        "token": "lakdsjlakjflakdsjffjklkadssldka"
    }
  ```

#### Articles App

**GET /articles/**

- **Description**: Show paginated list of articles
- **Authentication**: Not required
- **Query Parameters**:
  - `page`: (optional, default=1) the page of results to fetch

- **Example Response**:
  ```json
    {
        "count": 103, // count of articles
        "next": "link to next page",
        "previous": "link to previous page",
        "results": [
            {
                "id": 1,
                "user_rating": null, // only when user rating is authenticated and has rated the article
                "title": "article title",
                "body": "article body",
                "created_at": "2024-10-12T19:32:22.156378Z",
                "rating_count": 0, // count of rates on this article
                "rating_average": 0.0 // average rating of the article
            },
            ...
        ]
    }
  ```

**POST /articles/rate**

- **Description**: Submit Rating
- **Authentication**: Required
- **Body**: 
  - `article_id`
  - `score`: an integer between 0 to 5 as the rating of the article

- **Example Response**:
  ```json
    {
        "id": 1,
        "score": 2,
        "created_at": "2024-10-12T19:38:52.374566Z",
        "updated_at": "2024-10-12T19:38:52.374576Z",
        "article": 1
    }
  ```

## Configuration

### Formatting
Environment variables should be set in json style so that pydantict can parse them to python values. Pay attention to the examples in env-template file.

### Variables

#### Celry
- **CELERY_BROKER_REDIS**:
    * type: str
    * The redis url for celery to use as broker

#### DB
- **DB_USER**:
    * type: str
    * The redis url for celery to use as broker
- **DB_PASSWORD**:
    * type: str
    * The redis url for celery to use as broker
- **DB_NAME**:
    * type: str
    * The redis url for celery to use as broker
- **DB_HOST**:
    * type: str
    * The redis url for celery to use as broker
- **DB_PORT**:
    * type: integer
    * The redis url for celery to use as broker

#### Django
- **ALLOWED_HOSTS**:
    * type: list
    * List of allowed hosts
- **CORS_ALLOWED_ORIGINS**:
    * type: list
    * List of CORS allowed origins
- **CSRF_TRUSTED_ORIGINS**:
    * type: list
    * List of trusted origins
- **DEBUG**:
    * type: bool
    * Debug activation flag
- **SECRET_KEY**:
    * type: str
    * Encryption secret key of django (Create one for production and keep it secret)

#### Spam Rating Detector
- **SPAM_RATE_COUNT_LIMIT**:
    * type: int
    * Number of ratings of an article that need to be submitted before spam detection can work

- **SPAM_RATE_ZSCORE_BOUND**:
    * type: float
    * The z-score bound that determines if a new submitted rating is suspicious  

- **SPAM_RATE_PROB_DIFF_LIMIT**:
    * type: float
    * To confirm if an score is spam the real rate of its accurance is compared to the Normal Distribution PDF of that score for that article and if the difference is grater than this limit, the score is considered spam

- **SPAM_DETECTION_IS_ACTIVE**:
    * type: bool
    * If SPAM_DETECTION_IS_ACTIVE is false then the spam detection is deactivated.
- **SPAM_DETECTION_TASK_PERIOD_TIME**:
    * type: int
    * Defines intervals between periodic task of spam detection in minutes.

## Spam Detection

### Problem Exploration
Rating systems are prone to malicious spamming attacks for the purpose of boosting an article`s rating or decreasing it. 

One way to avoid this proablem is spam detection systems which are themselves a type of anomaly detection systems. 

With a bit of researching the similar proablems on the web I was introduced to many varaity of such systems and came across a [recent paper](https://www.sciencedirect.com/science/article/abs/pii/S0957417423017384) addressing this similar issue. There, it was explained that normal users' rating behaviour yields to a normal distribution of ratings. 

### Spam Detection Process
The spam detection system in this project uses the statistical fact that normall user ratings has a normal distribution and creates a two step process:

#### 1. Marking Suspicious Ratings
When a user submits a rating for an article, the normal distribution of the ratings of that article is considered and if the z-score of the new rating falls out of a reasonable bound(specified by **SPAM_RATE_ZSCORE_BOUND**), it is considered a probable spam. Other wise the rating is considered not spam. Probable spam ratings does not affect article rating but not spam ratings will immediately  affect article`s rating.

#### 2. Detect Real Spam from Probable Spams

Periodically(Interval time specified by **SPAM_DETECTION_TASK_PERIOD_TIME**) all probable spams are reevaluated to avoid false positives.

In this step if a spam campain is going on, many probable spams will be gathered and the **actual probability** of an out of bound rating will differ significantly with the normal PDF of that rating.

For example, take a suspicouse rating of 0 for article1, what will happen to this rating is this:

```
    actual_probability = count of ratings of article1 with the score of  0 / count of all ratings of article1

    probability_difference = actual_probability - noraml_pdf(0, article1)

```

Now if this probability difference is greater than a limit(specified by **SPAM_RATE_PROB_DIFF_LIMIT**) then the rating is considered a sure spam and else it is considered a not spam and will affect the article`s rating.

### Implementation Considrations

* For the first step to work synchronously, info about the normal distribution of the ratings should be accessable low effort. So ratings average, count and sum of squared mean differnces are saved in article tables and updated accordingly.

* Updating articles' rating info might cause race conditions and lead to inconsistancy. To avoid that F expressions are used.

* Updating articles' rating info if the rating is not spam happens synchronously. In order to avoid heavy queries on DB [online algorithms](https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#:~:text=to%20a%20degree.-,Welford%27s%20online%20algorithm,-%5Bedit%20source) were used to update articles' rating info.

* In order for this method to work, ratings should have a normal distribution which when an article`s rating count is low, does not exist. So, a limit of ratings per article is set that spam detection would only work after ratings exceed that limit(specified by **SPAM_RATE_COUNT_LIMIT**) 

### Imporvements

* Considering users' previous behaviours could make real spam detection more prcise. This can be anything from simply counting the users spam ratings to using complex data models to classify user as spammer.

* Tuning parameters with real data.

* Considering submission time of ratings as an statistical factor

* Including spam detection for updates requires more memory and computational power. This current version of system does not support spam detection for updates. Instead updated ratings inherit the previouse spam status. Including updates is a trade of between increasing db load and more accuracy that resolving depends of the usages of the system.
