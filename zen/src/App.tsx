import { Recommends } from "./components/Recommends";
import { SideMenu } from "./components/SideMenu";
import { Timeline } from "./components/TimeLine";
import { Provider } from "./components/ui/provider";
import { Box, HStack } from "@chakra-ui/react";

const sampleTweets = [
    {
        user: { name: "太郎", username: "taro", avatar: "/avatar1.jpg" },
        content: "今日はいい天気ですね！",
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000) // 2時間前
    },
    {
        user: { name: "花子", username: "hanako", avatar: "/avatar2.jpg" },
        content: "新しいプロジェクトが始まりました！",
        timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000) // 3時間前
    },
    {
        user: { name: "次郎", username: "jiro", avatar: "/avatar3.jpg" },
        content: "週末は友達とキャンプに行きます。",
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000) // 5時間前
    },
    {
        user: { name: "美咲", username: "misaki", avatar: "/avatar4.jpg" },
        content: "最近読んだ本がとても面白かったです。",
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000) // 1日前
    }
];

export default function App() {
    return (
        <Provider>
            <Box minH="100vh" bg="gray.50">
                <HStack gap={0} maxW="1200px" mx="auto">
                    <SideMenu />
                    <Timeline tweets={sampleTweets} />
                    <Recommends />
                </HStack>
            </Box>
        </Provider>
    )
}
