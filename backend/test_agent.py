
from agent.graph import graph


result = graph.invoke(
    {
        "message_text": "Black"
    },
    config={
        "configurable": {
            "thread_id": "shop_1_customer_test_user"
        }
    }
)

print("\nFinal Agent Output:")
print(result)


print("\nFinal Agent Output:")
print(result)
