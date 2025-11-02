-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Nov 02, 2025 at 07:45 AM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `lms_jepang`
--

-- --------------------------------------------------------

--
-- Table structure for table `certificates`
--

DROP TABLE IF EXISTS `certificates`;
CREATE TABLE IF NOT EXISTS `certificates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `class_id` int DEFAULT NULL,
  `certificate_number` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `issued_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `certificate_number` (`certificate_number`),
  KEY `student_id` (`student_id`),
  KEY `class_id` (`class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `classes`
--

DROP TABLE IF EXISTS `classes`;
CREATE TABLE IF NOT EXISTS `classes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `schedule` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `classes`
--

INSERT INTO `classes` (`id`, `name`, `schedule`, `description`, `created_at`) VALUES
(1, 'Kelas Reguler', 'Senin–Jumat, 08.00–14.00', 'Kelas umum untuk pelajar reguler.', '2025-10-26 20:51:56'),
(2, 'Kelas Karyawan', 'Senin–Jumat, 19.00–21.00', 'Kelas malam khusus karyawan.', '2025-10-26 20:51:56');

-- --------------------------------------------------------

--
-- Table structure for table `enrollments`
--

DROP TABLE IF EXISTS `enrollments`;
CREATE TABLE IF NOT EXISTS `enrollments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `class_id` int NOT NULL,
  `enrolled_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `class_id` (`class_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `enrollments`
--

INSERT INTO `enrollments` (`id`, `user_id`, `class_id`, `enrolled_at`) VALUES
(1, 179, 1, '2025-10-26 20:56:36'),
(2, 264, 2, '2025-11-02 13:00:05');

-- --------------------------------------------------------

--
-- Table structure for table `forum_comments`
--

DROP TABLE IF EXISTS `forum_comments`;
CREATE TABLE IF NOT EXISTS `forum_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int DEFAULT NULL,
  `body` text COLLATE utf8mb4_general_ci,
  `user_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `forum_posts`
--

DROP TABLE IF EXISTS `forum_posts`;
CREATE TABLE IF NOT EXISTS `forum_posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `body` text COLLATE utf8mb4_general_ci,
  `user_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `forum_replies`
--

DROP TABLE IF EXISTS `forum_replies`;
CREATE TABLE IF NOT EXISTS `forum_replies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `post_id` int NOT NULL,
  `user_id` int NOT NULL,
  `body` text NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `post_id` (`post_id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `materials`
--

DROP TABLE IF EXISTS `materials`;
CREATE TABLE IF NOT EXISTS `materials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `content` text COLLATE utf8mb4_general_ci,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `quizzes`
--

DROP TABLE IF EXISTS `quizzes`;
CREATE TABLE IF NOT EXISTS `quizzes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `quiz_answers`
--

DROP TABLE IF EXISTS `quiz_answers`;
CREATE TABLE IF NOT EXISTS `quiz_answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int DEFAULT NULL,
  `question_id` int DEFAULT NULL,
  `student_id` int DEFAULT NULL,
  `selected_option` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `is_correct` tinyint(1) DEFAULT NULL,
  `answered_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `quiz_questions`
--

DROP TABLE IF EXISTS `quiz_questions`;
CREATE TABLE IF NOT EXISTS `quiz_questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int DEFAULT NULL,
  `question` text COLLATE utf8mb4_general_ci,
  `option_a` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `option_b` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `option_c` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `option_d` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `option_e` text COLLATE utf8mb4_general_ci,
  `correct_option` char(1) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `quiz_scores`
--

DROP TABLE IF EXISTS `quiz_scores`;
CREATE TABLE IF NOT EXISTS `quiz_scores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int DEFAULT NULL,
  `student_id` int DEFAULT NULL,
  `score` float DEFAULT NULL,
  `graded_by` int DEFAULT NULL,
  `graded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
CREATE TABLE IF NOT EXISTS `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `due_date` datetime DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `task_submissions`
--

DROP TABLE IF EXISTS `task_submissions`;
CREATE TABLE IF NOT EXISTS `task_submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` int DEFAULT NULL,
  `student_id` int DEFAULT NULL,
  `file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `grade` float DEFAULT NULL,
  `graded_by` int DEFAULT NULL,
  `graded_at` datetime DEFAULT NULL,
  `score` decimal(5,2) DEFAULT NULL,
  `feedback` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `full_name` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bio` text COLLATE utf8mb4_general_ci,
  `avatar` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=328 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `role`, `full_name`, `bio`, `avatar`) VALUES
(1, 'sensei', 'scrypt:32768:8:1$B3zZnbWJI3THYwtD$7ab8982c124cd02f1b7a3b31f3f3b027e266118efb87d4ad8b4efd9a0205dd2a61e5d2783dbdf7c4daf8e2edf48b61db0990bd4d6a43127738c441dd9ae35eea', 'sensei', 'Sensei Ichiro', NULL, NULL),
(2, 'siswa', 'scrypt:32768:8:1$qneVDlihfTuVeYRY$ffca105ed6aad2eaf05aa9865cf1997016e33db8f52f02ec2a879141f763c35fa185cf7c7eb2858ac608ea2f2cd84c3bed7c7034521d2e9c69c68d404a13918d', 'student', 'Siswa Aiko', NULL, NULL),
(179, 'brianevandhika', 'scrypt:32768:8:1$YElkdgcquYyTJMTQ$c77cb4105832202e9ec4e10261632e62a7143eabd1a43777fdc6c080c37b223ccd91d958ddf0c8b10bd8d9ad2e7cdccfee6c95ebe7f2a6706f8f55e364d0d7d6', 'student', 'Brian Farrel Evandhika', NULL, NULL),
(233, 'admin', 'scrypt:32768:8:1$9mnLdq9P5GfSgSay$a10de984202ca5317b768647309259a87b4729e8905ae865837bdb14f9e4521a7ea0441f1d2f900f94d1f5e597b35260ba09854cd80de7b277fe0a0988c2cc7d', 'admin', 'Administrator', NULL, NULL),
(264, 'Daffa', 'scrypt:32768:8:1$zBASxTShqKwqXmgk$74d8eb5bb02593286e845cd731257568b38ed12d971318f096bfe278a35d281cb954b078f55fc2bf273d86d882d5fee3fcc235dd465a65193128617b28e49bde', 'student', 'Daffa Aryaputra', NULL, NULL);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `certificates`
--
ALTER TABLE `certificates`
  ADD CONSTRAINT `certificates_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `certificates_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `enrollments`
--
ALTER TABLE `enrollments`
  ADD CONSTRAINT `enrollments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `enrollments_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
