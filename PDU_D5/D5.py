"""
Imię i nazwisko
Rozwiązanie pracy domowej nr 5
"""

# 1.) Przygotowanie danych

# a) wykonaj import potrzebnych pakietów
import pandas as pd
import numpy as np
import os, os.path
import sqlite3
# b) wczytaj ramki danych, na których będziesz dalej pracował
Posts = pd.read_csv("Posts.csv.gz")
Posts.head()
Users = pd.read_csv("Users.csv.gz")
Users.head()
Comments = pd.read_csv("Comments.csv.gz")
Comments.head()
# c) przygotuj bazę danych zgodnie z instrukcją zamieszczoną w treści pracy domowej
baza = 'przyklad.db'
conn = sqlite3.connect(baza)
#Comments.to_sql("Comments", conn)
#Posts.to_sql("Posts", conn)
#Users.to_sql("Users", conn)
# 2.) Wyniki zapytań SQL

sql_1 = pd.read_sql_query("""SELECT Location, SUM(UpVotes) as TotalUpVotes
FROM Users
WHERE Location != ''
GROUP BY Location
ORDER BY TotalUpVotes DESC
LIMIT 10""", conn)


sql_2 = pd.read_sql_query("""SELECT STRFTIME('%Y', CreationDate) AS Year, STRFTIME('%m', CreationDate) AS Month,
COUNT(*) AS PostsNumber, MAX(Score) AS MaxScore
FROM Posts
WHERE PostTypeId IN (1, 2)
GROUP BY Year, Month
HAVING PostsNumber > 1000""", conn)


sql_3 = pd.read_sql_query("""SELECT Id, DisplayName, TotalViews
FROM (
SELECT OwnerUserId, SUM(ViewCount) as TotalViews
FROM Posts
WHERE PostTypeId = 1
GROUP BY OwnerUserId
) AS Questions
JOIN Users
ON Users.Id = Questions.OwnerUserId
ORDER BY TotalViews DESC
LIMIT 10""", conn)


sql_4 = pd.read_sql_query("""SELECT DisplayName, QuestionsNumber, AnswersNumber, Location, Reputation, UpVotes, DownVotes
FROM (
SELECT *
FROM (
SELECT COUNT(*) as AnswersNumber, OwnerUserId
FROM Posts
WHERE PostTypeId = 2
GROUP BY OwnerUserId
) AS Answers
JOIN
(
SELECT COUNT(*) as QuestionsNumber, OwnerUserId
FROM Posts
WHERE PostTypeId = 1
GROUP BY OwnerUserId
) AS Questions
ON Answers.OwnerUserId = Questions.OwnerUserId
WHERE AnswersNumber > QuestionsNumber
ORDER BY AnswersNumber DESC
LIMIT 5
) AS PostsCounts
JOIN Users
ON PostsCounts.OwnerUserId = Users.Id""", conn)


sql_5 = pd.read_sql_query("""SELECT Title, CommentCount, ViewCount, CommentsTotalScore, DisplayName, Reputation, Location
FROM (
SELECT Posts.OwnerUserId, Posts.Title, Posts.CommentCount, Posts.ViewCount,
CmtTotScr.CommentsTotalScore
FROM (
SELECT PostId, SUM(Score) AS CommentsTotalScore
FROM Comments
GROUP BY PostId
) AS CmtTotScr
JOIN Posts ON Posts.Id = CmtTotScr.PostId
WHERE Posts.PostTypeId=1
) AS PostsBestComments
JOIN Users ON PostsBestComments.OwnerUserId = Users.Id
ORDER BY CommentsTotalScore DESC
LIMIT 10""", conn)

conn.close()


# Uwaga: Zapytania powinny się wykonywać nie dłużej niż kilka sekund każde, jednak czasem występują problemy zależne od systemu, np. pod Linuxem zapytania 3 i 5 potrafią zająć odp. kilka minut i ponad godzinę. Żeby obejść ten problem wyniki zapytań mozna zapisac do tymczasowych plików pickle.

# Zapisanie każdej z ramek danych opisujących wyniki zapytań SQL do osobnego pliku pickle.
for i, df in enumerate([sql_1, sql_2, sql_3, sql_4, sql_5], 1):
    df.to_pickle(f'sql_{i}.pkl.gz')

# Wczytanie policzonych uprzednio wyników z plików pickle (możesz to zrobić, jeżeli zapytania wykonują się za długo).
sql_1, sql_2, sql_3, sql_4, sql_5 = [
    pd.read_pickle(f'sql_{i}.pkl.gz') for i in range(1, 5 + 1)
]

# 3.) Wyniki zapytań SQL odtworzone przy użyciu metod pakietu Pandas.

# zad. 1

try:
    x = Users.groupby('Location')['UpVotes'].sum().reset_index()
    x = x[x['Location'] != '']
    x = x.sort_values(by='UpVotes', ascending=False)
    x = x.head(10)
    x.reset_index(drop=True, inplace=True)
    x.columns = ['Location', 'TotalUpVotes']
    pandas_1 = x
    print (pandas_1.equals(sql_1) )

except Exception as e:
    print("Zad. 1: niepoprawny wynik.")
    print(e)

# zad. 2

try:
    x = Posts[Posts['PostTypeId'].isin([1, 2])]
    x = x[['CreationDate', 'Score', 'PostTypeId']]
    x['Year'] = x['CreationDate'].str[:4]
    x['Month'] = x['CreationDate'].str[5:7]
    x.drop(['CreationDate', 'PostTypeId'], axis=1, inplace=True)
    PostsNumber = x.groupby(['Year', 'Month']).size().reset_index(name='PostsNumber')
    MaxScore = x.groupby(['Year', 'Month']).agg({'Score': 'max'}).reset_index()
    MaxScore.rename(columns={'Score': 'MaxScore'}, inplace=True)
    y = pd.merge(PostsNumber, MaxScore, on=['Year', 'Month'])
    y.rename(columns={'Score': 'PostsNumber'}, inplace=True)
    y = y[y['PostsNumber'] > 1000]
    y.reset_index(drop=True, inplace=True)
    pandas_2 = y
    print (pandas_2.equals(sql_2) )

except Exception as e:
    print("Zad. 2: niepoprawny wynik.")
    print(e)

# zad. 3

try:
    Questions = Posts[Posts['PostTypeId'] == 1]
    Questions = Posts.groupby('OwnerUserId')['ViewCount'].sum().reset_index()
    Questions = Questions.sort_values('OwnerUserId')
    Questions.columns = ['OwnerUserId', 'TotalViews']
    x = pd.merge(Users, Questions, left_on='Id', right_on='OwnerUserId')
    x = x.sort_values('TotalViews', ascending=False)
    x = x.head(10)
    x.reset_index(drop=True, inplace=True)
    x = x[['Id', 'DisplayName', 'TotalViews']]
    pandas_3 = x
    print (pandas_3.equals(sql_3) )

except Exception as e:
    print("Zad. 3: niepoprawny wynik.")
    print(e)

# zad. 4

try:
    x = Posts[Posts['PostTypeId'] == 2]
    x = x.groupby('OwnerUserId').size().reset_index()
    x.columns = ['OwnerUserId', 'AnswersNumber']
    y = Posts[Posts['PostTypeId'] == 1]
    y = y.groupby('OwnerUserId').size().reset_index()
    y.columns = ['OwnerUserId', 'QuestionsNumber']
    z = pd.merge(x, y, on='OwnerUserId')
    z = z[z['AnswersNumber'] > z['QuestionsNumber']]
    a = pd.merge(z, Users, left_on='OwnerUserId', right_on='Id')
    a = a.sort_values('AnswersNumber', ascending=False)
    a = a.head(5)
    a.reset_index(drop=True, inplace=True)
    a = a[['DisplayName', 'QuestionsNumber', 'AnswersNumber', 'Location', 'Reputation', 'UpVotes', 'DownVotes']]
    pandas_4 = a
    print (pandas_4.equals(sql_4) )

except Exception as e:
    print("Zad. 4: niepoprawny wynik.")
    print(e)

# zad. 5

try:
    CmtTotScr = Comments.groupby('PostId')['Score'].sum().reset_index()
    CmtTotScr.columns = ['PostId', 'CommentsTotalScore']
    CmtTotScr = CmtTotScr.sort_values('PostId', ascending=False)
    x = pd.merge(Posts, CmtTotScr, left_on='Id', right_on='PostId')
    x = x[x['PostTypeId'] == 1]
    x = x[['OwnerUserId', 'Title', 'CommentCount', 'ViewCount', 'CommentsTotalScore']]
    y = pd.merge(Users, x, left_on='Id', right_on='OwnerUserId')
    y = y.sort_values('CommentsTotalScore', ascending=False)
    y = y.head(10)
    y = y[['Title', 'CommentCount', 'ViewCount', 'CommentsTotalScore', 'DisplayName', 'Reputation', 'Location']]
    y.reset_index(drop=True, inplace=True)
    pandas_5 = y
    print (pandas_5.equals(sql_5) )

except Exception as e:
    print("Zad. 5: niepoprawny wynik.")
    print(e)

