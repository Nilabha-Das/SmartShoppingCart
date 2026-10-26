
package com.smartshopping.backend.controller;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import tools.jackson.databind.JsonNode;

@RestController
@RequestMapping("/api/ai")
@CrossOrigin(origins = "http://localhost:5173")
public class AiController {

    private final RestClient restClient;

    public AiController() {
        this.restClient = RestClient.create("http://localhost:8000");
    }

    @GetMapping("/health")
    public JsonNode checkAiHealth() {
        return restClient.get()
                .uri("/health")
                .retrieve()
                .body(JsonNode.class);
    }

    @GetMapping("/shopping/search")
    public JsonNode searchProducts(
            @RequestParam String message,
            @RequestParam(name = "session_id", defaultValue = "default")
            String sessionId,
            @RequestParam(name = "ask_preferences", defaultValue = "false")
            boolean askPreferences) {

        return restClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/shopping/search")
                        .queryParam("message", message)
                        .queryParam("session_id", sessionId)
                        .queryParam("ask_preferences", askPreferences)
                        .build())
                .retrieve()
                .body(JsonNode.class);
    }

    @PostMapping("/shopping/preferences/answer")
    public JsonNode answerPreference(
            @RequestParam(name = "session_id") String sessionId,
            @RequestParam String preference,
            @RequestParam String answer) {

        return restClient.post()
                .uri(uriBuilder -> uriBuilder
                        .path("/shopping/preferences/answer")
                        .queryParam("session_id", sessionId)
                        .queryParam("preference", preference)
                        .queryParam("answer", answer)
                        .build())
                .retrieve()
                .body(JsonNode.class);
    }

    @GetMapping("/recommend/content/{productId}")
    public JsonNode recommendContent(
            @PathVariable String productId) {

        return restClient.get()
                .uri("/recommend/content/{productId}", productId)
                .retrieve()
                .body(JsonNode.class);
    }

    @GetMapping("/recommend/collaborative/{customerId}")
    public JsonNode recommendCollaborative(
            @PathVariable String customerId) {

        return restClient.get()
                .uri("/recommend/collaborative/{customerId}", customerId)
                .retrieve()
                .body(JsonNode.class);
    }

    @GetMapping("/recommend/hybrid/{customerId}")
    public JsonNode recommendHybrid(
            @PathVariable String customerId) {

        return restClient.get()
                .uri("/recommend/hybrid/{customerId}", customerId)
                .retrieve()
                .body(JsonNode.class);
    }
}
