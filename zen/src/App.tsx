import { Col, Flex, Layout, Row } from "antd";
import Chat from "./Chat";
import TimeLine, { type TweetData } from "./TimeLine";

const { Header, Footer, Content } = Layout;

const sampleTweets: TweetData[] = [
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() },
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() },
    { user: { name: "abc", username: "def" }, content: "ghijk", detail: "lmnop", timestamp: new Date() }
]

export const App = () => {
    return (
        <Flex gap="middle" wrap>
            <Layout>
                <Header>Header</Header>
                <Content>
                    <Row>
                        <Col span={18}><Chat /></Col>
                        <Col span={6}><TimeLine tweets={sampleTweets} /></Col>
                    </Row>
                </Content>
                <Footer>Footer</Footer>
            </Layout>
        </Flex>
    );
}

export default App;
