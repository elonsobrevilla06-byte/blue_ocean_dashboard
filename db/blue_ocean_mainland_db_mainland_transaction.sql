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
-- Table structure for table `mainland_transaction`
--

DROP TABLE IF EXISTS `mainland_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mainland_transaction` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` varchar(50) DEFAULT NULL,
  `type_of_transaction` varchar(50) DEFAULT NULL,
  `main_guest_information` json DEFAULT NULL,
  `add_on_guest` json DEFAULT NULL,
  `total_net_billing` double DEFAULT NULL,
  `total_amount_paid` double DEFAULT NULL,
  `total_change` double DEFAULT NULL,
  `mode_of_payment` varchar(50) DEFAULT NULL,
  `reference_number` varchar(50) DEFAULT NULL,
  `status` enum('pending','confirmed','billout','cancelled') DEFAULT NULL,
  `reservation_datetime` datetime DEFAULT NULL,
  `notes` varchar(250) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `deck_assigned` varchar(50) DEFAULT NULL,
  `table_assigned` varchar(50) DEFAULT NULL,
  `access_type` varchar(50) DEFAULT NULL,
  `assigned_card_number` varchar(50) DEFAULT NULL,
  `attended_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mainland_transaction`
--

LOCK TABLES `mainland_transaction` WRITE;
/*!40000 ALTER TABLE `mainland_transaction` DISABLE KEYS */;
INSERT INTO `mainland_transaction` VALUES (2,'RSV-2603310253','reservation','{\"pax\": \"2\", \"email\": \"hasselmann@klinikimkurpark.de\", \"notes\": \"\", \"phone\": \"+491723721333\", \"country\": \"Philippines\", \"duration\": 0, \"lastName\": \"Hasselmann\", \"firstName\": \"Jens\", \"discountId\": null, \"amount_paid\": 0, \"ticket_amount\": 800, \"discountAmount\": 0, \"transaction_id\": \"RSV-2603310253\", \"transactiondate\": \"2026-03-31\", \"reservation_time\": \"09:00\", \"services_availed\": [], \"transaction_screenshot\": \"\"}','[{\"pax\": 1, \"email\": \"hasselmann@klinikimkurpark.de\", \"notes\": \"\", \"phone\": \"+49 1723721333\", \"country\": \"Germany\", \"duration\": 0, \"lastName\": \"Klotz\", \"firstName\": \"Simone\", \"discountId\": null, \"amount_paid\": 0, \"ticket_amount\": 800.0, \"discountAmount\": 0, \"transaction_id\": \"RSV-2603310253\", \"transactiondate\": \"2026-03-31\", \"reservation_time\": \"09:00\", \"services_availed\": []}]',1600,0,-1600,'paypal','5AS22901BP659180X','confirmed','2026-04-08 00:00:00','N/A','2025-04-08 00:00:00','maindeck','-','dayaccess',NULL,'N/A'),(3,'RSV-2603310303','reservation','{\"pax\": \"1\", \"email\": \"hasselmann@klinikimkurpark.de\", \"notes\": \"1 dog\", \"phone\": \"+49 1723721333\", \"country\": \"Germany\", \"duration\": \"720\", \"lastName\": \"H\", \"firstName\": \"J\", \"discountId\": null, \"amount_paid\": 0, \"ticket_amount\": 1000, \"discountAmount\": 0, \"transaction_id\": \"RSV-2603310303\", \"transactiondate\": \"2026-04-16\", \"reservation_time\": \"17:00\", \"services_availed\": [], \"transaction_screenshot\": \"\"}',NULL,1000,0,-1000,'paypal','7AL21474RV392154R','pending','2026-04-16 00:00:00','1 dog','2026-04-08 00:00:00','maindeck','Seat 1 - FREE SEATING - BAR STOOL','nightaccess',NULL,'N/A');
/*!40000 ALTER TABLE `mainland_transaction` ENABLE KEYS */;
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
