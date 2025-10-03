import { HStack, IconButton, VStack, Text, Box } from "@chakra-ui/react";
import { LuMessageCircle, LuRepeat2, LuHeart, LuShare } from "react-icons/lu";
import { useState, useEffect } from "react";

interface User {
    name: string;
    username: string;
    avatar?: string;
}

interface TweetData {
    user: User;
    content: string;
    timestamp: Date;
}

function formatRelativeTime(date: Date): string {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
        return `${diffInSeconds}秒前`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes}分前`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours}時間前`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days}日前`;
    }
}

function Tweet({ user, content, timestamp }: Readonly<TweetData>) {
    const [relativeTime, setRelativeTime] = useState(formatRelativeTime(timestamp));

    useEffect(() => {
        const updateRelativeTime = () => {
            setRelativeTime(formatRelativeTime(timestamp));
        };

        updateRelativeTime();

        const interval = setInterval(updateRelativeTime, 60000);

        return () => clearInterval(interval);
    }, [timestamp]);

    return (
        <Box w="full" borderY="1px" borderColor="gray.200" p={4}>
            <HStack alignItems="start" gap={3}>
                <Box w="48px" h="48px" borderRadius="full" bg="gray.300" />
                <VStack alignItems="start" flex={1} gap={1}>
                    <HStack>
                        <Text fontWeight="bold">{user.name}</Text>
                        <Text color="gray.500">@{user.username}</Text>
                        <Text color="gray.500">·</Text>
                        <Text color="gray.500">{relativeTime}</Text>
                    </HStack>
                    <Text>{content}</Text>
                </VStack>
            </HStack>
            <HStack gap={0} pt={2} w="full" justifyContent="space-around">
                <IconButton variant="ghost" size="sm">
                    <LuMessageCircle />
                </IconButton>
                <IconButton variant="ghost" size="sm">
                    <LuRepeat2 />
                </IconButton>
                <IconButton variant="ghost" size="sm">
                    <LuHeart />
                </IconButton>
                <IconButton variant="ghost" size="sm">
                    <LuShare />
                </IconButton>
            </HStack>
        </Box>
    )
}

export function Timeline({ tweets }: Readonly<{ tweets: TweetData[] }>) {
    return (
        <Box flex={1} borderRight="1px" borderColor="gray.200" bg="white" h="100vh">
            <Box p={4} borderBottom="1px" borderColor="gray.200" bg="white" position="sticky" top={0} zIndex={1}>
                <Text fontSize="xl" fontWeight="bold">ホーム</Text>
            </Box>
            <Box overflow="auto" h="calc(100vh - 80px)">
                <VStack gap={0} alignItems="stretch">
                    {tweets.map((tweet, index) => (
                        <Tweet key={`tweet-${index}`} {...tweet} />
                    ))}
                </VStack>
            </Box>
        </Box>
    )
}
