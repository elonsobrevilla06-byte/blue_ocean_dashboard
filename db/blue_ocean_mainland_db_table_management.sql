-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: blue_ocean_mainland_db
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `table_management`
--

DROP TABLE IF EXISTS `table_management`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `table_management` (
  `table_id` int NOT NULL AUTO_INCREMENT,
  `table_name` varchar(50) DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `location` enum('skydeck','maindeck') DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `transaction_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`table_id`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_management`
--

LOCK TABLES `table_management` WRITE;
/*!40000 ALTER TABLE `table_management` DISABLE KEYS */;
INSERT INTO `table_management` VALUES (1,'T1 - Front Facade',4,'maindeck','Available',NULL),(2,'T2 - Front Facade',4,'maindeck','Available',NULL),(3,'T3 - Front Facade',4,'maindeck','Available',NULL),(4,'T4 - Front Facade',4,'maindeck','Available',NULL),(5,'T5 - Front Facade',4,'maindeck','Available',NULL),(6,'T6 - Front Facade',4,'maindeck','Available',NULL),(7,'T7 - Front Facade',4,'maindeck','Available',NULL),(8,'T8 - Sunset View Free Seating',4,'maindeck','Available',NULL),(9,'T9 - Sunset View Free Seating',4,'maindeck','Available',NULL),(10,'T10 - Sunset View Free Seating',4,'maindeck','Available',NULL),(11,'T11 - Sunset View Free Seating',4,'maindeck','Available',NULL),(12,'T12 - Sunset View Free Seating',4,'maindeck','Available',NULL),(13,'T13 - Jacuzzi Couch Free Seating',4,'maindeck','Available',NULL),(14,'T14 - Jacuzzi Couch Free Seating',4,'maindeck','Available',NULL),(15,'T15 - Front Facade',4,'maindeck','Available',NULL),(16,'T16 - Front Facade',4,'maindeck','Available',NULL),(17,'T17 - Front Facade',4,'maindeck','Available',NULL),(18,'T18 - Front Facade',4,'maindeck','Available',NULL),(19,'T19 - Front Facade',4,'maindeck','Available',NULL),(20,'T20 - Front Facade',4,'maindeck','Available',NULL),(21,'C1 - Sunset View',12,'maindeck','Available',NULL),(22,'C2 - Sunset View',12,'maindeck','Available',NULL),(23,'C3 - Sunset View',12,'maindeck','Available',NULL),(24,'C4 - Jacuzzi Couch',12,'maindeck','Available',NULL),(25,'C5 - Jacuzzi Couch',12,'maindeck','Available',NULL),(26,'C6 - Jacuzzi Couch',12,'maindeck','Available',NULL),(27,'C7 - Jacuzzi Couch',12,'maindeck','Available',NULL),(28,'C8 - Sea Couch',12,'maindeck','Available',NULL),(29,'C9 - Sea Couch',12,'maindeck','Available',NULL),(30,'C10 - Sea Couch',12,'maindeck','Available',NULL),(31,'C11 - Sea Couch',12,'maindeck','Available',NULL),(32,'Seat 1 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(33,'Seat 2 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(34,'Seat 3 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(35,'Seat 4 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(36,'Seat 5 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(37,'Seat 6 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(38,'Seat 7 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(39,'Seat 8 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(40,'Seat 9 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(41,'Seat 10 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(42,'Seat 11 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(43,'Seat 12 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(44,'Seat 13 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(45,'Seat 14 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(46,'Seat 15 - Free Seating - Bar Stool',1,'maindeck','Available',NULL),(47,'S1 - Sunset View',12,'skydeck','Available',NULL),(48,'S2 - Sunset View',12,'skydeck','Available',NULL),(49,'S3 - Sunset View',12,'skydeck','Available',NULL),(50,'S4 - Sunset View',12,'skydeck','Available',NULL),(51,'S5 - Sunset View',12,'skydeck','Available',NULL),(52,'S6 - Sunset View',12,'skydeck','Available',NULL),(53,'S7 - Sunset View',12,'skydeck','Available',NULL),(54,'C1 - Sunset View South',12,'skydeck','Available',NULL),(55,'C2 - Sunset View South',12,'skydeck','Available',NULL),(56,'C3 - Sunset View South',12,'skydeck','Available',NULL),(57,'T3 - DJS POD',4,'skydeck','Available',NULL),(58,'T4 - DJS POD',4,'skydeck','Available',NULL),(59,'T15 - DJS POD',4,'skydeck','Available',NULL),(60,'T16 - DJS POD',4,'skydeck','Available',NULL),(61,'T1 - Free Seating',4,'skydeck','Available',NULL),(62,'T2 - Free Seating',4,'skydeck','Available',NULL),(63,'T5 - Free Seating',4,'skydeck','Available',NULL),(64,'T6 - Free Seating',4,'skydeck','Available',NULL),(65,'T7 - Free Seating',4,'skydeck','Available',NULL),(66,'T8 - Free Seating',4,'skydeck','Available',NULL),(67,'T9 - Free Seating',4,'skydeck','Available',NULL),(68,'T10 - Free Seating',4,'skydeck','Available',NULL),(69,'T11 - Free Seating',4,'skydeck','Available',NULL),(70,'T12 - Free Seating',4,'skydeck','Available',NULL),(71,'T13 - Free Seating',4,'skydeck','Available',NULL),(72,'T14 - Free Seating',4,'skydeck','Available',NULL),(73,'C4 - Paradise View',12,'skydeck','Available',NULL),(74,'Seat 1 - Free Seating - Bar Stool',1,'skydeck','Available',NULL),(75,'Seat 2 - Free Seating - Bar Stool',1,'skydeck','Available',NULL),(76,'Seat 3 - Free Seating - Bar Stool',1,'skydeck','Available',NULL),(77,'Seat 4 - Free Seating - Bar Stool',1,'skydeck','Available',NULL),(78,'Seat 5 - Free Seating - Bar Stool',1,'skydeck','Available',NULL);
/*!40000 ALTER TABLE `table_management` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-15  8:55:10
