import { Flex } from "antd";
import TimeLine, { type TweetData } from "./TimeLine";

const sampleTweets: TweetData[] = [
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() },
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() },
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() }
]

export const App = () => {
    return (
        <Flex gap="middle" wrap>
            <TimeLine tweets={sampleTweets} />
        </Flex>
    );
}

export default App;
