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
-- Table structure for table `employee_drawer_history`
--

DROP TABLE IF EXISTS `employee_drawer_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_drawer_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `drawer_id` varchar(50) DEFAULT NULL,
  `register` varchar(250) DEFAULT NULL,
  `cashier` varchar(250) DEFAULT NULL,
  `start_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime DEFAULT NULL,
  `starting_cash` float DEFAULT '0',
  `ending_balance` float DEFAULT '0',
  `total_sales` float DEFAULT '0',
  `cash_variance` float DEFAULT '0',
  `status` varchar(50) DEFAULT 'Active',
  `current_balance` float DEFAULT NULL,
  `assigned_to` varchar(250) DEFAULT NULL,
  `safe_deposit` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_drawer_history`
--

LOCK TABLES `employee_drawer_history` WRITE;
/*!40000 ALTER TABLE `employee_drawer_history` DISABLE KEYS */;
INSERT INTO `employee_drawer_history` VALUES (1,'Float','Floating','Juanitos Dela Cruz','2026-04-10 11:18:00','2026-04-11 08:50:57',5000,9500,0,7500,'Closed',2000,'Floating Bar',345757),(2,'Float','Floating','Margie Lapore','2026-04-11 00:55:12','2026-04-11 08:56:19',5000,5000,0,0,'Closed',5000,'Floating Bar',NULL),(3,'Float','Floating','Juanitos Dela Cruz','2026-04-11 00:57:53','2026-04-11 08:58:16',5000,5000,0,0,'Closed',5000,'Floating Bar',NULL),(4,'Float','Floating','Margie Lapore','2026-04-11 01:00:22','2026-04-11 09:03:48',5000,5000,0,0,'Closed',5000,'Floating Bar',NULL),(5,'Float','Floating','Kazia Orsos','2026-04-11 01:08:50','2026-04-11 09:09:05',5000,5000,0,0,'Closed',5000,'Floating Bar',NULL),(6,'Float','Floating','Gretchille Suarez','2026-04-11 01:10:46','2026-04-11 09:10:57',5000,53000,0,48000,'Closed',5000,'Floating Bar',NULL),(7,'Float','Floating','Gretchille Suarez','2026-04-11 01:19:51','2026-04-11 09:22:33',5000,0,0,0,'Closed',5000,'Floating Bar',NULL),(8,'Float','Floating','Juanitos Dela Cruz','2026-04-11 03:21:12','2026-04-11 11:21:29',5000,23232300000000,0,23232300000000,'Closed',5000,'Floating Bar',NULL),(9,'Float','Floating','Juanitos Dela Cruz','2026-04-11 03:22:45','2026-04-11 11:22:55',5000,6000,0,1000,'Closed',5000,'Floating Bar',NULL),(10,'Mainland_drawer','Mainland','Kazia Orsos','2026-04-13 12:24:34','2026-04-13 20:26:26',5000,0,0,0,'Closed',5000,'Mainland',NULL),(11,'Mainland_drawer','Mainland','Juanitos Dela Cruz','2026-04-13 12:43:23',NULL,5000,0,0,0,'Active',5169,'Mainland',NULL);
/*!40000 ALTER TABLE `employee_drawer_history` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-15  8:55:12
