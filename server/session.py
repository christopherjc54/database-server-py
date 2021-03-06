#!/usr/bin/env python3

import secrets
import datetime
import logging

import mysql.connector

from __main__ import Global

class Session:

    def create(username, datetime_offset=datetime.timedelta(days=1, hours=0)):
        sessionID = secrets.token_hex(int(32/2)) ## each byte gets converted to two hex digits
        expDateTime = datetime.datetime.now() + datetime_offset
        try:
            Global.cursor.execute(
                "INSERT INTO Session (username, sessionID, expDateTime) VALUES (%s, %s, %s);",
                (username, sessionID, expDateTime)
            )
        except mysql.connector.errors.IntegrityError: ## used for duplicate key errors, foreign key constraint errors (n/a here), and data too long errors (n/a here)
            return "" ## session already exists
                      ## this error will only occur when Session("username") is set as primary key or unique
        return sessionID

    def validate(username, sessionID):
        Global.cursor.execute(
            "SELECT sessionID, expDateTime FROM Session WHERE username = %s AND sessionID = %s ORDER BY id;",
            (username, sessionID)
        )
        result = Global.cursor.fetchall()
        if len(result) > 0:
            for db_sessionID, db_expDateTime in result:
                if(db_expDateTime > datetime.datetime.now()):
                    return True
                else:
                    logging.info("deleting an expired session for \"" + username + "\"")
                    Session.delete(db_sessionID)
            logging.error("all sessions for \"" + username + "\" expired")
        else:
            logging.error("session not found")
        return False

    def update(sessionID, datetime_offset=datetime.timedelta(days=1, hours=0)):
        expDateTime = datetime.datetime.now() + datetime_offset
        Global.cursor.execute(
            "UPDATE Session SET expDateTime = %s WHERE sessionID = %s;",
            (expDateTime, sessionID)
        )

    def delete(sessionID):
        Global.cursor.execute(
            "DELETE FROM Session WHERE sessionID = %s;",
            (sessionID,)
        )

    def delete_all_expired():
        Global.cursor.execute("SELECT username, sessionID, expDateTime FROM Session ORDER BY id;")
        result = Global.cursor.fetchall()
        for db_username, db_sessionID, db_expDateTime in result:
            if(db_expDateTime < datetime.datetime.now()):
                logging.info("deleting an expired session for \"" + db_username + "\"")
                Session.delete(db_sessionID)

    def test(username):
        expDateTimeSQL = "SELECT expDateTime FROM Session WHERE sessionID = %s;"

        sessionID = Session.create(username)
        logging.debug("sessionID: " + sessionID)
        
        Global.cursor.execute(expDateTimeSQL, (sessionID,))
        result = Global.cursor.fetchall()
        logging.debug("expDateTime: " + str(result[0][0]))
        logging.debug("valid session? " + str(Session.validate(username, sessionID)))

        Session.update(sessionID, datetime.timedelta(days=2))
        Global.cursor.execute(expDateTimeSQL, (sessionID,))
        result = Global.cursor.fetchall()
        logging.debug("expDateTime: " + str(result[0][0]))
        logging.debug("valid session? " + str(Session.validate(username, sessionID)))

        Session.update(sessionID, datetime.timedelta(days=-5))
        Global.cursor.execute(expDateTimeSQL, (sessionID,))
        result = Global.cursor.fetchall()
        logging.debug("expDateTime: " + str(result[0][0]))
        logging.debug("valid session? " + str(Session.validate(username, sessionID)))

        Session.delete(sessionID)
        logging.debug("valid session? " + str(Session.validate(username, sessionID)))