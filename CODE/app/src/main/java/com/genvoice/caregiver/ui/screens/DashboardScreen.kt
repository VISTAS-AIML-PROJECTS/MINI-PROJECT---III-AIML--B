package com.genvoice.caregiver.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.viewmodels.DashboardViewModel
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * Dashboard Screen - Shows senior's recent conversations (Blueprint Architecture)
 * UPDATED: Displays full message transcripts with intents
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadDashboard()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "GenVoice Caregiver",
                        fontWeight = FontWeight.Bold
                    )
                },
                actions = {
                    IconButton(onClick = { viewModel.loadDashboard() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                }
            )
        }
    ) { padding ->
        when {
            uiState.isLoading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Loading...",
                        style = MaterialTheme.typography.titleLarge
                    )
                }
            }

            uiState.error != null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "Error loading data",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.error
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = uiState.error ?: "Unknown error",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { viewModel.loadDashboard() }) {
                            Text("Retry")
                        }
                    }
                }
            }

            else -> {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Senior Info Card
                    item {
                        SeniorInfoCard(
                            seniorName = uiState.seniorName ?: "Loading...",
                            lastCheckIn = uiState.lastCheckIn
                        )
                    }

                    // Recent Conversations Header
                    item {
                        Text(
                            text = "Recent Conversations",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(vertical = 8.dp)
                        )
                    }

                    // Conversation List
                    if (uiState.conversations.isEmpty()) {
                        item {
                            Text(
                                text = "No conversations yet",
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        items(uiState.conversations) { conversation ->
                            ConversationCard(
                                conversation = conversation,
                                onClick = { viewModel.selectConversation(conversation) }
                            )
                        }
                    }
                }
            }
        }

        // Show conversation details when a conversation is selected
        uiState.selectedConversation?.let { conversation ->
            ConversationDetailDialog(
                conversation = conversation,
                onDismiss = { viewModel.clearSelection() }
            )
        }
    }
}

@Composable
fun SeniorInfoCard(
    seniorName: String,
    lastCheckIn: String?
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Avatar
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = seniorName.take(1).uppercase(),
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onPrimary,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            Column {
                Text(
                    text = seniorName,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = if (lastCheckIn != null) {
                        "Last check-in: ${formatDateTime(lastCheckIn)}"
                    } else {
                        "No check-ins yet"
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                )
            }
        }
    }
}

@Composable
fun ConversationCard(
    conversation: ConversationDetails,
    onClick: () -> Unit
) {
    val conv = conversation.conversation
    val userMessages = conversation.messages.filter { it.speaker == "user" }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Time and Status
                Column {
                    Text(
                        text = formatDateTime(conv.completedAt ?: conv.startedAt),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "${conversation.messageCount} messages",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                // Status Badge
                ConversationStatusBadge(status = conv.status)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Show detected intents
            val intents = userMessages.mapNotNull { it.intent }.distinct()
            if (intents.isNotEmpty()) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    intents.take(3).forEach { intent ->
                        IntentChip(intent = intent)
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            // Show urgent or concerning messages
            val urgentMessages = userMessages.filter {
                it.intent in listOf("URGENT_SYMPTOM", "PHYSICAL_DISCOMFORT", "NEGATIVE", "LONELY")
            }
            if (urgentMessages.isNotEmpty()) {
                urgentMessages.take(1).forEach { msg ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                when (msg.intent) {
                                    "URGENT_SYMPTOM" -> Color(0xFFFFEBEE)
                                    "PHYSICAL_DISCOMFORT" -> Color(0xFFFFF3E0)
                                    else -> Color(0xFFF3E5F5)
                                }
                            )
                            .padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = when (msg.intent) {
                                "URGENT_SYMPTOM" -> "🚨"
                                "PHYSICAL_DISCOMFORT" -> "⚠️"
                                "NEGATIVE" -> "😔"
                                "LONELY" -> "💭"
                                else -> "💬"
                            },
                            style = MaterialTheme.typography.titleMedium,
                            modifier = Modifier.padding(end = 8.dp)
                        )
                        Text(
                            text = msg.content,
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            } else {
                // Show preview of first user message
                if (userMessages.isNotEmpty()) {
                    Text(
                        text = userMessages.first().content,
                        style = MaterialTheme.typography.bodySmall,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun ConversationStatusBadge(status: String) {
    val (backgroundColor, textColor, displayText) = when (status) {
        "completed" -> Triple(Color(0xFF4CAF50), Color.White, "Completed")
        "active" -> Triple(Color(0xFF2196F3), Color.White, "Active")
        "urgent" -> Triple(Color(0xFFF44336), Color.White, "Urgent")
        else -> Triple(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.colorScheme.onSurfaceVariant, status)
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .background(backgroundColor)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            text = displayText,
            style = MaterialTheme.typography.labelMedium,
            color = textColor,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun IntentChip(intent: String) {
    val (backgroundColor, icon) = when (intent) {
        "POSITIVE" -> Pair(Color(0xFFE8F5E9), "😊")
        "NEGATIVE" -> Pair(Color(0xFFFFEBEE), "😔")
        "LONELY" -> Pair(Color(0xFFF3E5F5), "💭")
        "PHYSICAL_DISCOMFORT" -> Pair(Color(0xFFFFF3E0), "⚠️")
        "ASSISTANCE_NEEDED" -> Pair(Color(0xFFE3F2FD), "🤝")
        "URGENT_SYMPTOM" -> Pair(Color(0xFFFFEBEE), "🚨")
        else -> Pair(Color(0xFFF5F5F5), "💬")
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(backgroundColor)
            .padding(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = icon, fontSize = 12.sp)
            Text(
                text = intent.lowercase().replace("_", " "),
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
fun ConversationDetailDialog(
    conversation: ConversationDetails,
    onDismiss: () -> Unit
) {
    val conv = conversation.conversation

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Column {
                Text(
                    text = "Conversation Details",
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = formatDateTime(conv.startedAt),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        },
        text = {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Status
                item {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Status:",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        ConversationStatusBadge(status = conv.status)
                    }
                }

                // Message count
                item {
                    DetailRow(
                        label = "Messages",
                        value = "${conversation.messageCount} total"
                    )
                }

                item {
                    Divider(modifier = Modifier.padding(vertical = 8.dp))
                }

                // Full transcript header
                item {
                    Text(
                        text = "Full Transcript:",
                        fontWeight = FontWeight.SemiBold,
                        style = MaterialTheme.typography.titleSmall
                    )
                }

                // Messages
                items(conversation.messages) { message ->
                    MessageBubble(message = message)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Close")
            }
        }
    )
}

@Composable
fun MessageBubble(message: ConversationMessageItem) {
    val isUser = message.speaker == "user"
    val backgroundColor = if (isUser) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = if (isUser) Alignment.End else Alignment.Start
    ) {
        // Speaker label with intent
        Row(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = if (isUser) "Senior" else "GenVoice",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            if (isUser && message.intent != null) {
                IntentChip(intent = message.intent)
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        // Message content
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(12.dp))
                .background(backgroundColor)
                .padding(12.dp)
                .widthIn(max = 280.dp)
        ) {
            Text(
                text = message.content,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Composable
fun DetailRow(label: String, value: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium
        )
    }
}

fun formatDateTime(dateTimeString: String): String {
    return try {
        val dateTime = LocalDateTime.parse(dateTimeString, DateTimeFormatter.ISO_DATE_TIME)
        dateTime.format(DateTimeFormatter.ofPattern("MMM dd, yyyy h:mm a"))
    } catch (e: Exception) {
        dateTimeString
    }
}
