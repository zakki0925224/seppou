package main

import (
	"sync"
	"time"
)

type RateLimiter struct {
	requests []time.Time
	maxReqs  int
	mu       sync.Mutex
}

func NewRateLimiter(maxRequests int) *RateLimiter {
	return &RateLimiter{
		requests: []time.Time{},
		maxReqs:  maxRequests,
	}
}

func (rl *RateLimiter) Allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()

	// delete logs older than 1s
	cutoff := now.Add(-1 * time.Second)
	var recentRequests []time.Time
	for _, t := range rl.requests {
		if t.After(cutoff) {
			recentRequests = append(recentRequests, t)
		}
	}
	rl.requests = recentRequests

	if len(rl.requests) < rl.maxReqs {
		rl.requests = append(rl.requests, now)
		return true
	}

	return false
}
