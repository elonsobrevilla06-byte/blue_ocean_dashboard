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
-- Table structure for table `employee_management`
--

DROP TABLE IF EXISTS `employee_management`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_management` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `firstName` varchar(50) NOT NULL,
  `lastName` varchar(50) NOT NULL,
  `contact_number` varchar(15) DEFAULT NULL,
  `email` varchar(50) DEFAULT NULL,
  `status` enum('Active','Inactive') DEFAULT 'Active',
  `position` varchar(50) DEFAULT NULL,
  `department` varchar(50) DEFAULT NULL,
  `assigned_to` varchar(250) DEFAULT 'N/A',
  `starting_cash` float DEFAULT '0',
  `cash_variance` float DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee_management`
--

LOCK TABLES `employee_management` WRITE;
/*!40000 ALTER TABLE `employee_management` DISABLE KEYS */;
INSERT INTO `employee_management` VALUES (1,'EMP1000','123456','Juanitos','Dela Cruz','09123456789','juan@email.com','Active','cashier','Floating Bar','N/A',0,0),(2,'EMP1001','123456','Elaine','Dela Cruz','09123456789','juan@email.com','Active','waiter','Floating Bar','N/A',40,40),(3,'EMP1002','123456','Dianne','Dela Cruz','09123456789','juan@email.com','Active','manager','Floating Bar','N/A',0,0),(4,'EMP1003','123456','Arjunren','Valdez','09553750917','arjunrenvon@gmail.com','Active','cashier','Floating Bar','N/A',0,0),(5,'EMP1004','123456','Elon','Sobrevilla','09123456789','elon@gmail.com','Active','waiter','Floating Bar','N/A',0,0),(7,'BOB-2026-0007','1','Melchor','Alip','','','Active','manager','Floating Bar','N/A',0,0),(8,'BOB-2026-0015','1','John Paul','Diosan','','','Active','manager','Floating Bar','N/A',0,0),(9,'BOB-2026-0014','1','Mellan Joy','Lapidez','','','Active','manager','Floating Bar','N/A',0,0),(10,'BOB-2026-0013','1','Rexan Gleem','Gaid','','','Active','manager','Floating Bar','N/A',0,0),(11,'BOB-2026-0033','1','Joy','Eleuterio','','','Active','cashier','Floating Bar','N/A',0,0),(12,'BOB-2026-0027','1989','Krisia','Favila','','','Active','cashier','Floating Bar','N/A',0,0),(13,'BOB-2026-0041','1','Abegail','Abique','','','Active','cashier','Floating Bar','N/A',0,0),(14,'BOB-2026-0042','1','Gretchille','Suarez','','','Active','cashier','Floating Bar','N/A',0,0),(15,'BOB-2026-0043','1221','Margie','Lapore','','','Active','cashier','Floating Bar','N/A',0,0),(16,'BOB-2026-0061','1','Kazia','Orsos','','','Active','cashier','Floating Bar','N/A',0,0),(17,'BOB-2026-0037','1','Emerson','Duqueza','','','Active','waiter','Floating Bar','N/A',0,0),(18,'BOB-2026-0038','1','Jhon Mark','Atabilo','','','Active','waiter','Floating Bar','N/A',0,0),(19,'BOB-2026-0039','1','Cherylene','Fernandez','','','Active','waiter','Floating Bar','N/A',0,0),(20,'BOB-2026-0046','29','Daizer Raye','Paglicawan','','','Active','waiter','Floating Bar','N/A',0,0),(21,'BOB-2026-0040','1','Noemie','Crisostomo','','','Active','waiter','Floating Bar','N/A',0,0),(22,'BOB-2026-0035','1','Jayzer','Gamora','','','Active','Waiter','Floating Bar','N/A',0,0),(31,'BOB-2026-0025','1','Kenneth John Mart','Jusos',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(32,'BOB-2026-0026','1','Armie Rose','Rey',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(33,'BOB-2026-0028','1','Anna Mae','Dela Fuente',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(34,'BOB-2026-0029','8','Joey','Elijan',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(35,'BOB-2026-0030','1','Joraly','Angeles',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(36,'BOB-2026-0031','1','Prince Charles','Lim',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(37,'BOB-2026-0032','27','Cherry Ann','Lumactod',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0),(38,'BOB-2026-0034','1','Dimee','Dela Cruz',NULL,NULL,'Active','Waiter','Floating Bar','N/A',0,0);
/*!40000 ALTER TABLE `employee_management` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-15  8:55:11
